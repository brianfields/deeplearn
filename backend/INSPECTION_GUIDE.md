# Bite-Sized Content Inspection Guide

This guide explains the easiest ways to inspect what bite-sized content has been generated for your syllabi.

## 🔍 Inspection Methods

### 1. **Quick Command-Line Inspection** (Fastest)

```bash
# Show all learning paths
python quick_inspect.py --paths

# Show bite-sized content summary
python quick_inspect.py --content

# Show specific topic details
python quick_inspect.py --topic <topic_id>

# Show everything
python quick_inspect.py --all
```

**Example Output:**
```
🎓 Learning Paths:
1. Machine Learning Fundamentals
   📝 5 topics
   📚 5 with bite-sized content
   🗓️  2024-01-15 10:30:45
```

### 2. **Interactive Inspector** (Most Detailed)

```bash
python inspect_bite_sized_content.py
```

This launches an interactive menu where you can:
- Browse all learning paths
- View bite-sized content summaries
- Inspect specific topics in detail
- See recent topics

### 3. **Database Direct Access** (Advanced)

```bash
# Install sqlite3 command-line tool if needed
# Then explore the database directly

sqlite3 bite_sized_topics.db

# Useful queries:
.schema
SELECT title, user_level, creation_strategy FROM topics;
SELECT component_type, COUNT(*) FROM components GROUP BY component_type;
```

### 4. **File System Inspection**

```bash
# Learning paths are stored as JSON files
ls -la .learning_data/

# Bite-sized content is in SQLite database
ls -la bite_sized_topics.db
```

## 📊 What Gets Created

When you create a syllabus, the system automatically generates:

### For Each Topic (First 5):
- **Didactic Snippet**: Teaching-focused explanation
- **Glossary**: Key terms and definitions
- **Storage**: SQLite database with full content
- **References**: Learning path JSON includes topic IDs

### Storage Structure:
```
.learning_data/           # Learning paths (JSON files)
├── path_abc123.json
├── path_def456.json
└── ...

bite_sized_topics.db      # Bite-sized content (SQLite)
├── topics table         # Topic metadata
└── components table     # Content components
```

## 🚀 Quick Start

1. **Create a learning path** through the web interface
2. **Run quick inspection**:
   ```bash
   python quick_inspect.py --all
   ```
3. **Get topic ID** from the output
4. **Inspect specific topic**:
   ```bash
   python quick_inspect.py --topic <topic_id>
   ```

## 🔧 What to Look For

### ✅ Successful Generation:
- Topics show `has_bite_sized_content: true`
- Database contains topic and component entries
- Components include didactic snippets and glossaries
- Frontend shows "Enhanced Content" badges

### ❌ Troubleshooting:
- No `.learning_data` folder = No learning paths created
- No `bite_sized_topics.db` = No bite-sized content generated
- Empty database = Content generation failed
- Missing components = Partial generation

## 📱 Frontend Inspection

You can also inspect content through the web interface:

1. **Open a learning path** in the frontend
2. **Look for green "Enhanced Content" badges** on topics
3. **Check the bite-sized content summary section**
4. **Verify the statistics** (topics generated, strategy, user level)

## 🧪 Testing

Run the integration test to verify everything works:

```bash
python tests/test_bite_sized_integration.py
```

This will create test content and verify the complete workflow.

## 📝 Example Workflow

```bash
# 1. Create learning path (through web interface)
# 2. Quick check
python quick_inspect.py --paths

# 3. Detailed inspection
python inspect_bite_sized_content.py

# 4. Specific topic analysis
python quick_inspect.py --topic topic_abc123
```

## 🎯 Key Files

- `quick_inspect.py` - Fast command-line inspection
- `inspect_bite_sized_content.py` - Interactive detailed inspector
- `tests/test_bite_sized_integration.py` - Integration testing
- `.learning_data/` - Learning path storage
- `bite_sized_topics.db` - Bite-sized content database

## 💡 Tips

- Use `--all` for a complete overview
- Topic IDs are shown in the inspection output
- The interactive inspector is best for detailed exploration
- Quick inspect is perfect for development and debugging
- Check both learning paths AND bite-sized content for complete picture