<template>
  <el-container class="app-layout">
    <el-aside width="240px" class="sidebar">
      <div class="logo">
        <span class="logo-text">纪检办公助手</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="var(--color-warm-silver)"
        active-text-color="var(--color-terracotta)"
        :collapse-transition="false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能对话</span>
        </el-menu-item>
        <el-sub-menu index="knowledge-base">
          <template #title>
            <el-icon><FolderOpened /></el-icon>
            <span>知识库管理</span>
          </template>
          <el-menu-item index="/documents">文档列表</el-menu-item>
          <el-menu-item index="/kb-search">知识库检索</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="user-management">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/users">用户列表</el-menu-item>
          <el-menu-item index="/users/roles">角色权限</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="system-settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/settings">通用设置</el-menu-item>
          <el-menu-item index="/settings/model">模型配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    <el-container class="content-area">
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <div class="header-right">
          <div class="avatar">
            <el-icon size="18"><UserFilled /></el-icon>
          </div>
          <span class="username">管理员</span>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, ChatDotRound, FolderOpened, User, Setting, UserFilled } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/documents/') && path !== '/documents') return '/documents'
  return path
})

const titleMap: Record<string, string> = {
  '/dashboard': '首页',
  '/chat': '智能对话',
  '/documents': '文档列表',
  '/kb-search': '知识库检索',
  '/users': '用户管理',
  '/settings': '系统设置',
}

const pageTitle = computed(() => {
  const path = route.path
  if (path.startsWith('/documents/')) return '文档详情'
  return titleMap[path] || ''
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
}

.sidebar {
  background: var(--color-deep-dark);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--color-dark-surface);
}

.logo-text {
  font-family: var(--font-serif);
  font-size: var(--text-h2);
  font-weight: 500;
  color: var(--color-ivory);
  letter-spacing: 0.02em;
}

.content-area {
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--color-ivory);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border-cream);
  padding: 0 var(--space-24);
  height: var(--el-header-height);
}

.header-title {
  font-family: var(--font-serif);
  font-size: var(--text-h1);
  font-weight: 500;
  color: var(--color-near-black);
  line-height: var(--lh-heading);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  color: var(--color-olive-gray);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-comfort);
  background: var(--color-warm-sand);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-charcoal);
}

.username {
  font-size: var(--text-caption);
  color: var(--color-olive-gray);
}

.main {
  background: var(--color-parchment);
  padding: var(--space-24);
}
</style>
