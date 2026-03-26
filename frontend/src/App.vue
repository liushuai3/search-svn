<template>
  <div class="app">
    <Layout>
      <Layout.Header role="banner" style="height: 64px; display: flex; align-items: center; padding: 0 24px; background: #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; font-size: 18px; color: #1890ff;">SVN 文件搜索系统</h1>
      </Layout.Header>
      <Layout>
        <Layout.Sider 
          width="200" 
          style="background: #fff; box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);"
          role="navigation"
          aria-label="主导航"
        >
          <Menu
            mode="inline"
            :selected-keys="[currentMenu]"
            style="height: 100%; border-right: none;"
            @select="handleMenuSelect"
            role="menubar"
            aria-label="功能菜单"
          >
            <Menu.Item key="config" role="menuitem">
              <template #icon>
                <SettingOutlined aria-hidden="true" />
              </template>
              SVN 设置
            </Menu.Item>
            <Menu.Item key="scan" role="menuitem">
              <template #icon>
                <ScanOutlined aria-hidden="true" />
              </template>
              文件扫描
            </Menu.Item>
            <Menu.Item key="search" role="menuitem">
              <template #icon>
                <SearchOutlined aria-hidden="true" />
              </template>
              文件搜索
            </Menu.Item>
          </Menu>
        </Layout.Sider>
        <Layout.Content 
          id="main-content"
          role="main"
          tabindex="-1"
          style="padding: 24px; background: #f0f2f5; height: calc(100vh - 64px); overflow: hidden;"
        >
          <component :is="currentComponent" />
        </Layout.Content>
      </Layout>
    </Layout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { SettingOutlined, ScanOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { Layout, Menu } from 'ant-design-vue'
import SVNConfig from './views/SVNConfig.vue'
import FileScan from './views/FileScan.vue'
import FileSearch from './views/FileSearch.vue'

const currentMenu = ref('search')

const currentComponent = computed(() => {
  switch (currentMenu.value) {
    case 'config':
      return SVNConfig
    case 'scan':
      return FileScan
    case 'search':
      return FileSearch
    default:
      return FileSearch
  }
})

const handleMenuSelect = ({ key }) => {
  currentMenu.value = key
}

// 监听菜单切换事件（从子组件触发）
const handleChangeMenu = (event) => {
  currentMenu.value = event.detail
}

onMounted(() => {
  window.addEventListener('changeMenu', handleChangeMenu)
})

onUnmounted(() => {
  window.removeEventListener('changeMenu', handleChangeMenu)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* 焦点样式 - 无障碍 */
*:focus-visible {
  outline: 2px solid #1890ff;
  outline-offset: 2px;
}

/* 减少动画 - 无障碍 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
