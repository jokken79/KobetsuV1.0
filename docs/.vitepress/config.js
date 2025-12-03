const { defineConfig } = require('vitepress')

module.exports = defineConfig({
  title: 'UNS Kobetsu Integrated',
  description: 'Comprehensive documentation for the UNS Kobetsu Keiyakusho system',
  lang: 'en',
  
  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      { 
        text: 'User Guides', 
        items: [
          { text: 'Contract Management', link: '/guides/contracts' },
          { text: 'Employee Management', link: '/guides/employees' },
          { text: 'Reports & Analytics', link: '/guides/reports' }
        ]
      },
      { 
        text: 'API Documentation', 
        items: [
          { text: 'Overview', link: '/api/' },
          { text: 'Authentication', link: '/api/authentication' },
          { text: 'Endpoints', link: '/api/endpoints' },
          { text: 'OpenAPI Spec', link: '/api/openapi' }
        ]
      },
      { 
        text: 'Development', 
        items: [
          { text: 'Setup', link: '/development/setup' },
          { text: 'Architecture', link: '/development/architecture' },
          { text: 'Contributing', link: '/development/contributing' }
        ]
      },
      { 
        text: 'Deployment', 
        items: [
          { text: 'Docker', link: '/deployment/docker' },
          { text: 'Production', link: '/deployment/production' },
          { text: 'Monitoring', link: '/deployment/monitoring' }
        ]
      }
    ],

    sidebar: {
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Introduction', link: '/api/' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Contracts', link: '/api/contracts' },
            { text: 'Employees', link: '/api/employees' },
            { text: 'Factories', link: '/api/factories' },
            { text: 'Documents', link: '/api/documents' },
            { text: 'OpenAPI Specification', link: '/api/openapi' }
          ]
        }
      ],
      '/guides/': [
        {
          text: 'User Guides',
          items: [
            { text: 'Contract Management', link: '/guides/contracts' },
            { text: 'Employee Management', link: '/guides/employees' },
            { text: 'Document Generation', link: '/guides/documents' },
            { text: 'Reports & Analytics', link: '/guides/reports' }
          ]
        }
      ],
      '/development/': [
        {
          text: 'Development Guide',
          items: [
            { text: 'Development Setup', link: '/development/setup' },
            { text: 'Project Architecture', link: '/development/architecture' },
            { text: 'Database Schema', link: '/development/database' },
            { text: 'Testing Guide', link: '/development/testing' },
            { text: 'Contributing', link: '/development/contributing' }
          ]
        }
      ],
      '/deployment/': [
        {
          text: 'Deployment Guide',
          items: [
            { text: 'Docker Deployment', link: '/deployment/docker' },
            { text: 'Production Setup', link: '/deployment/production' },
            { text: 'Environment Configuration', link: '/deployment/environment' },
            { text: 'Monitoring & Logging', link: '/deployment/monitoring' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/uns-kikaku/UNS-Kobetsu-Integrated' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: `Copyright © ${new Date().getFullYear()} UNS Team`
    },

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/uns-kikaku/UNS-Kobetsu-Integrated/edit/main/docs/:path'
    },

    carbonAds: {
      code: 'your-carbon-code',
      placement: 'right'
    }
  },

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    },
    lineNumbers: true,
    config: (md) => {
      // you can use markdown-it plugins
      md.use(require('markdown-it-task-lists'))
    }
  },

  vite: {
    define: {
      __VUE_OPTIONS_API__: false
    },
    server: {
      host: true,
      port: 5173
    },
    build: {
      minify: 'terser',
      chunkSizeWarningLimit: 1000
    }
  }
})