type QueryFilters = Record<string, unknown>;

/** Hierarchical keys, so invalidating `lists()` covers every filtered list under the scope. */
export const createQueryKeys = <Scope extends string>(scope: Scope) => ({
  all: [scope] as const,
  lists: () => [scope, 'list'] as const,
  list: (filters: QueryFilters = {}) => [scope, 'list', filters] as const,
  details: () => [scope, 'detail'] as const,
  detail: (id: string) => [scope, 'detail', id] as const,
});
