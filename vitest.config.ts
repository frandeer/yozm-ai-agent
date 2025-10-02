import { defineConfig } from 'vitest/config'
import type { Plugin } from 'vite'

const markdownAsString = (): Plugin => ({
  name: 'vitest-markdown-as-string',
  enforce: 'pre',
  transform(code, id) {
    if (id.endsWith('.md')) {
      return {
        code: `export default ${JSON.stringify(code)};`,
        map: null
      }
    }
    return null
  }
})

export default defineConfig({
  plugins: [markdownAsString()],
  resolve: {
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.md']
  },
  test: {
    environment: 'node'
  }
})
