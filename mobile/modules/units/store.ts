import { create } from 'zustand';

export type UnitsView = 'list' | 'detail' | 'progress';

interface State {
  view: UnitsView;
  selectedUnitId: string | null;
  searchQuery: string;
}

interface Actions {
  setView(view: UnitsView): void;
  selectUnit(id: string | null): void;
  setSearch(query: string): void;
}

export const useUnitsStore = create<State & Actions>(set => ({
  view: 'list',
  selectedUnitId: null,
  searchQuery: '',
  setView: view => set({ view }),
  selectUnit: id => set({ selectedUnitId: id }),
  setSearch: q => set({ searchQuery: q }),
}));
