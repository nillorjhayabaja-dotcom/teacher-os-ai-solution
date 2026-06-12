// ============================================================
// TeacherOS — Tenant Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { Tenant } from "@/types";

interface TenantState {
  currentTenant: Tenant | null;
  tenants: Tenant[];
  isLoading: boolean;
}

interface TenantActions {
  setCurrentTenant: (tenant: Tenant) => void;
  setTenants: (tenants: Tenant[]) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

type TenantStore = TenantState & TenantActions;

const initialState: TenantState = {
  currentTenant: null,
  tenants: [],
  isLoading: false,
};

export const useTenantStore = create<TenantStore>()((set) => ({
  ...initialState,

  setCurrentTenant: (currentTenant) => set({ currentTenant }),
  setTenants: (tenants) => set({ tenants }),
  setLoading: (isLoading) => set({ isLoading }),
  clear: () => set({ ...initialState }),
}));