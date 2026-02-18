import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './constants';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
export const setToken = (token) => {
  if (token) {
    localStorage.setItem('token', token);
    apiClient.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    localStorage.removeItem('token');
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

export const getToken = () => localStorage.getItem('token');

// User id management (persist alongside token)
export const setUserId = (userId) => {
  if (userId == null) {
    localStorage.removeItem('user_id');
  } else {
    localStorage.setItem('user_id', String(userId));
  }
};

export const getUserId = () => {
  const v = localStorage.getItem('user_id');
  return v == null ? null : parseInt(v, 10);
};

export const logout = () => {
  setToken(null);
  setUserId(null);
};

export const login = async (username, password) => {
  const res = await apiClient.post(API_ENDPOINTS.LOGIN, { username, password });
  // backend returns { token, user_id }
  const data = res.data || {};
  if (data.token) setToken(data.token);
  if (data.user_id) setUserId(data.user_id);
  return data;
};

// Projects
export const getProjects = () => {
  // Normalize paginated DRF responses so callers always receive an array
  return apiClient.get(API_ENDPOINTS.PROJECTS).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const getProjectDefaultMaterials = (projectId) => {
  return apiClient.get(API_ENDPOINTS.PROJECT_MATERIALS(projectId)).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

// Shopping Lists
export const createShoppingList = (data) => {
  return apiClient.post(API_ENDPOINTS.SHOPPING_LISTS, data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const getShoppingList = (id) => {
  return apiClient.get(API_ENDPOINTS.SHOPPING_LIST_DETAIL(id)).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const updateShoppingList = (id, data) => {
  return apiClient.patch(API_ENDPOINTS.SHOPPING_LIST_DETAIL(id), data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const getShoppingListsForUser = (userId) => {
  return apiClient.get(API_ENDPOINTS.SHOPPING_LISTS_USER, { params: { user_id: userId } }).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

// Shopping List Items
export const addShoppingListItem = (listId, data) => {
  return apiClient.post(API_ENDPOINTS.SHOPPING_LIST_ITEMS(listId), data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

// Store Product Search
export const searchProducts = (query, store = 'amazon') => {
  return apiClient.get(API_ENDPOINTS.STORE_SEARCH, {
    params: { q: query, store: store }
  }).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const updateShoppingListItem = (itemId, data) => {
  return apiClient.patch(API_ENDPOINTS.SHOPPING_LIST_ITEM_DETAIL(itemId), data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const deleteShoppingListItem = (itemId) => {
  return apiClient.delete(API_ENDPOINTS.SHOPPING_LIST_ITEM_DETAIL(itemId)).then((res) => ({
    ...res,
    data: res.data && (res.data.results || res.data),
  }));
};

// User Materials
export const getUserMaterials = (userId) => {
  return apiClient.get(API_ENDPOINTS.USER_MATERIALS(userId)).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const createUserMaterial = (userId, data) => {
  return apiClient.post(API_ENDPOINTS.USER_MATERIALS(userId), data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const updateUserMaterial = (userId, materialId, data) => {
  return apiClient.patch(API_ENDPOINTS.USER_MATERIAL_UPDATE(userId, materialId), data).then((res) => ({
    ...res,
    data: res.data.results || res.data,
  }));
};

export const deleteUserMaterial = (userId, materialId) => {
  return apiClient.delete(API_ENDPOINTS.USER_MATERIAL_UPDATE(userId, materialId)).then((res) => ({
    ...res,
    data: res.data && (res.data.results || res.data),
  }));
};

// Error handler utility
export const handleApiError = (error) => {
  if (error.response) {
    return error.response.data?.detail || error.response.statusText || 'An error occurred';
  } else if (error.request) {
    return 'No response from server. Please check your connection.';
  } else {
    return error.message || 'An error occurred';
  }
};
