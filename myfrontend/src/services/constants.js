// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_ENDPOINTS = {
  PROJECTS: '/api/projects/',
  PROJECT_MATERIALS: (projectId) => `/api/projects/${projectId}/default-materials/`,
  SHOPPING_LISTS: '/api/shopping-lists/',
  SHOPPING_LIST_DETAIL: (id) => `/api/shopping-lists/${id}/`,
  SHOPPING_LISTS_USER: '/api/shopping-lists/user/',
  SHOPPING_LIST_ITEMS: (id) => `/api/shopping-lists/${id}/items/`,
  SHOPPING_LIST_ITEM_DETAIL: (itemId) => `/api/shopping-list-items/${itemId}/`,
  USER_MATERIALS: (userId) => `/api/user-materials/${userId}/`,
  USER_MATERIAL_UPDATE: (userId, materialId) => `/api/user-materials/${userId}/${materialId}/`,
  STORE_SEARCH: '/api/store-search/search/',
  LOGIN: '/api/auth/login/',
};
