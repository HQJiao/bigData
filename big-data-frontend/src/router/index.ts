import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
        { path: 'chat', name: 'chat', component: () => import('../views/ChatView.vue') },
        { path: 'documents', name: 'documents', component: () => import('../views/DocumentListView.vue') },
        { path: 'documents/:id', name: 'document-detail', component: () => import('../views/DocumentDetailView.vue') },
        { path: 'kb-search', name: 'kb-search', component: () => import('../views/KbSearchView.vue') },
        { path: 'users', name: 'users', component: () => import('../views/UserManagementView.vue') },
        { path: 'users/roles', name: 'roles', component: () => import('../views/UserManagementView.vue') },
        { path: 'settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
        { path: 'settings/model', name: 'model-config', component: () => import('../views/SettingsView.vue') },
      ],
    },
  ],
})

export default router
