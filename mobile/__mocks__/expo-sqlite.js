const databases = new Map();

function createState() {
  return {
    tables: new Map(),
  };
}

function ensureTable(state, name) {
  if (!state.tables.has(name)) {
    state.tables.set(name, new Map());
  }
  return state.tables.get(name);
}

function getPrimaryKey(tableName) {
  switch (tableName) {
    case 'units':
    case 'lessons':
    case 'assets':
    case 'outbox':
    case '_migrations':
      return 'id';
    case 'metadata':
      return 'key';
    default:
      return 'id';
  }
}

function toResult(rows, rowsAffected = 0, insertId = null) {
  return {
    rows: {
      length: rows.length,
      item: index => rows[index],
      _array: rows,
    },
    rowsAffected,
    insertId,
  };
}

function parseColumns(segment) {
  return segment.split(',').map(column => column.trim().replace(/`/g, ''));
}

function handleCreateTable(state, sql) {
  const match = sql.match(/CREATE TABLE IF NOT EXISTS (\w+)/i);
  if (!match) {
    throw new Error(`Unsupported CREATE TABLE statement: ${sql}`);
  }
  const tableName = match[1];
  ensureTable(state, tableName);
  return toResult([]);
}

function handleInsert(state, sql, params, replace = false) {
  const match = sql.match(
    /INSERT(?: OR REPLACE)? INTO (\w+) \(([^)]+)\) VALUES \(([^)]+)\)/i
  );
  if (!match) {
    throw new Error(`Unsupported INSERT statement: ${sql}`);
  }
  const tableName = match[1];
  const columns = parseColumns(match[2]);
  const table = ensureTable(state, tableName);
  const row = {};
  columns.forEach((column, index) => {
    row[column] = params[index];
  });
  const primaryKey = getPrimaryKey(tableName);
  const key = row[primaryKey];
  if (replace || tableName === 'metadata') {
    table.set(key, row);
  } else {
    if (table.has(key)) {
      throw new Error(`Duplicate key ${key} for table ${tableName}`);
    }
    table.set(key, row);
  }
  return toResult([], 1, key ?? null);
}

function handleDelete(state, sql, params) {
  const match = sql.match(/DELETE FROM (\w+)(?: WHERE (.+))?/i);
  if (!match) {
    throw new Error(`Unsupported DELETE statement: ${sql}`);
  }
  const tableName = match[1];
  const table = ensureTable(state, tableName);
  if (!match[2]) {
    table.clear();
    return toResult([], table.size);
  }

  const condition = match[2].trim();
  let rowsAffected = 0;
  if (/schema_version < \?/i.test(condition)) {
    const threshold = params[0];
    for (const [key, value] of [...table.entries()]) {
      if ((value.schema_version ?? 0) < threshold) {
        table.delete(key);
        rowsAffected += 1;
      }
    }
  } else if (/unit_id = \?/i.test(condition)) {
    const unitId = params[0];
    for (const [key, value] of [...table.entries()]) {
      if (value.unit_id === unitId) {
        table.delete(key);
        rowsAffected += 1;
      }
    }
  } else if (/id = \?/i.test(condition)) {
    const id = params[0];
    if (table.delete(id)) {
      rowsAffected = 1;
    }
  }
  return toResult([], rowsAffected);
}

function handleUpdate(state, sql, params) {
  const match = sql.match(/UPDATE (\w+) SET (.+) WHERE (.+)/i);
  if (!match) {
    throw new Error(`Unsupported UPDATE statement: ${sql}`);
  }
  const tableName = match[1];
  const table = ensureTable(state, tableName);
  const setClause = match[2];
  const whereClause = match[3];
  const assignments = setClause.split(',').map(part => part.trim());

  let targetId = null;
  let paramIndex = assignments.length;

  if (/id = \?/i.test(whereClause)) {
    targetId = params[paramIndex];
  } else if (/unit_id = \?/i.test(whereClause)) {
    targetId = params[paramIndex];
  }

  const row = table.get(targetId);
  if (!row) {
    return toResult([], 0);
  }

  assignments.forEach((assignment, index) => {
    const [column] = assignment.split('=');
    row[column.trim()] = params[index];
  });
  table.set(targetId, row);
  return toResult([], 1);
}

function compareValues(a, b) {
  if (a === b) {
    return 0;
  }
  if (a === undefined || a === null) {
    return -1;
  }
  if (b === undefined || b === null) {
    return 1;
  }
  if (typeof a === 'number' && typeof b === 'number') {
    return a - b;
  }
  return String(a).localeCompare(String(b));
}

function handleSelect(state, sql, params) {
  const countMatch = sql.match(/SELECT COUNT\(\*\) as count FROM (\w+)/i);
  if (countMatch) {
    const table = ensureTable(state, countMatch[1]);
    return toResult([{ count: table.size }]);
  }

  const metadataMatch = sql.match(/SELECT value FROM metadata WHERE key = \?/i);
  if (metadataMatch) {
    const table = ensureTable(state, 'metadata');
    const value = table.get(params[0]);
    if (!value) {
      return toResult([]);
    }
    return toResult([{ value: value.value }]);
  }

  // Match SELECT column(s) FROM table with optional WHERE/ORDER BY/LIMIT
  const selectMatch = sql.match(
    /SELECT (.+?) FROM (\w+)(?: WHERE (.+?))?(?:\s+ORDER BY (\w+)(?: (ASC|DESC))?)?(?: LIMIT (\d+))?;?$/i
  );
  if (!selectMatch) {
    throw new Error(`Unsupported SELECT statement: ${sql}`);
  }

  const columns = selectMatch[1].trim();
  const tableName = selectMatch[2];
  const table = ensureTable(state, tableName);
  const whereClause = selectMatch[3];
  const orderColumn = selectMatch[4];
  const orderDirection = (selectMatch[5] || 'ASC').toUpperCase();
  const limit = selectMatch[6] ? parseInt(selectMatch[6], 10) : undefined;

  let rows = Array.from(table.values());

  if (whereClause) {
    const conditions = whereClause.split('AND').map(part => part.trim());
    rows = rows.filter(row => {
      let paramIndex = 0; // Reset paramIndex for each row
      return conditions.every(condition => {
        const comparison = condition.match(/(\w+)\s*(=|<=|<)\s*\?/);
        if (!comparison) {
          return true;
        }
        const [, column, operator] = comparison;
        const value = params[paramIndex];
        paramIndex += 1;
        if (operator === '=' && row[column] !== value) {
          return false;
        }
        if (operator === '<' && !(row[column] < value)) {
          return false;
        }
        if (operator === '<=' && !(row[column] <= value)) {
          return false;
        }
        return true;
      });
    });
  }

  if (orderColumn) {
    rows.sort((a, b) => {
      const comparison = compareValues(a[orderColumn], b[orderColumn]);
      return orderDirection === 'DESC' ? -comparison : comparison;
    });
  }

  if (typeof limit === 'number') {
    rows = rows.slice(0, limit);
  }

  // If selecting specific columns (not *), project only those columns
  if (columns !== '*') {
    const columnList = columns.split(',').map(c => c.trim());
    rows = rows.map(row => {
      const projected = {};
      columnList.forEach(col => {
        projected[col] = row[col];
      });
      return projected;
    });
  }

  return toResult(rows);
}

function normalizeSql(sql) {
  return sql.trim().replace(/\s+/g, ' ');
}

function executeStatement(state, sql, params) {
  const normalized = normalizeSql(sql);
  if (/^PRAGMA/i.test(normalized)) {
    return toResult([]);
  }
  if (/^CREATE TABLE/i.test(normalized)) {
    return handleCreateTable(state, normalized);
  }
  if (/^INSERT OR REPLACE/i.test(normalized)) {
    return handleInsert(state, normalized, params, true);
  }
  if (/^INSERT INTO/i.test(normalized)) {
    return handleInsert(state, normalized, params, false);
  }
  if (/^ALTER TABLE units ADD COLUMN unit_payload TEXT;?$/i.test(normalized)) {
    return toResult([]);
  }
  if (/^DELETE FROM/i.test(normalized)) {
    return handleDelete(state, normalized, params);
  }
  if (/^UPDATE/i.test(normalized)) {
    return handleUpdate(state, normalized, params);
  }
  if (/^SELECT/i.test(normalized)) {
    return handleSelect(state, normalized, params);
  }

  throw new Error(`Unsupported SQL statement: ${sql}`);
}

function createTransaction(state, resolve, reject) {
  return {
    executeSql(sql, params = [], success, error) {
      try {
        const result = executeStatement(state, sql, params);
        if (success) {
          success(this, result);
        }
      } catch (err) {
        if (error) {
          const shouldContinue = error(this, err);
          if (shouldContinue === false) {
            return false;
          }
        }
        reject(err);
        return false;
      }
      return true;
    },
  };
}

function openDatabase(name) {
  if (!databases.has(name)) {
    databases.set(name, createState());
  }
  const state = databases.get(name);

  return {
    transaction(callback, errorCallback, successCallback) {
      try {
        const tx = createTransaction(
          state,
          () => {},
          errorCallback || (() => {})
        );
        callback(tx);
        if (successCallback) {
          successCallback();
        }
      } catch (error) {
        if (errorCallback) {
          errorCallback(error);
        }
      }
    },
    readTransaction(callback, errorCallback, successCallback) {
      this.transaction(callback, errorCallback, successCallback);
    },
    close() {
      // no-op for mock
    },
    // expo-sqlite v15 synchronous API
    execSync(sql) {
      executeStatement(state, sql, []);
    },
    runSync(sql, params = []) {
      const result = executeStatement(state, sql, params);
      return {
        changes: result.rowsAffected || 0,
        lastInsertRowId: result.insertId || undefined,
      };
    },
    getAllSync(sql, params = []) {
      const result = executeStatement(state, sql, params);
      return result.rows._array || [];
    },
    getFirstSync(sql, params = []) {
      const result = executeStatement(state, sql, params);
      return result.rows.length > 0 ? result.rows._array[0] : null;
    },
    closeSync() {
      // no-op for mock
    },
  };
}

module.exports = {
  openDatabase,
  openDatabaseSync: openDatabase,
  openDatabaseAsync: async name => openDatabase(name),
};
