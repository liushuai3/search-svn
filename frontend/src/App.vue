<template>
  <div class="app">
    <Layout>
      <Layout.Header style="height: 64px; display: flex; align-items: center; padding: 0 24px; background: #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; font-size: 18px; color: #1890ff;">SVN 文件搜索系统</h1>
      </Layout.Header>
      <Layout>
        <Layout.Sider width="200" style="background: #fff; box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);">
          <Menu
            mode="inline"
            :selected-keys="[currentMenu]"
            style="height: 100%; border-right: none;"
            @select="handleMenuSelect"
          >
            <Menu.Item key="config">
              <template #icon>
                <SettingOutlined />
              </template>
              SVN 设置
            </Menu.Item>
            <Menu.Item key="scan">
              <template #icon>
                <ScanOutlined />
              </template>
              文件扫描
            </Menu.Item>
            <Menu.Item key="search">
              <template #icon>
                <SearchOutlined />
              </template>
              文件搜索
            </Menu.Item>
          </Menu>
        </Layout.Sider>
        <Layout.Content style="padding: 24px; background: #f0f2f5; min-height: calc(100vh - 64px);">
          <component :is="currentComponent" />
        </Layout.Content>
      </Layout>
    </Layout>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
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
}
</style>
