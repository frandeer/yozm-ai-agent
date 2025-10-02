import { defineConfig } from 'vitepress'
import { readdirSync, statSync } from 'fs'
import { join, relative, parse } from 'path'

// 마크다운 파일을 재귀적으로 스캔하여 사이드바 구조를 생성하는 함수
function generateSidebar(dir: string, baseDir: string = dir): any[] {
  const items: any[] = []
  
  try {
    const files = readdirSync(dir)
    
    for (const file of files) {
      const fullPath = join(dir, file)
      const stat = statSync(fullPath)
      
      // 숨김 파일/폴더 및 .vitepress 폴더 제외
      if (file.startsWith('.') || file === 'node_modules') {
        continue
      }
      
      if (stat.isDirectory()) {
        // 하위 디렉토리의 파일들을 재귀적으로 스캔
        const subItems = generateSidebar(fullPath, baseDir)
        
        if (subItems.length > 0) {
          items.push({
            text: formatTitle(file),
            collapsed: false,
            items: subItems
          })
        }
      } else if (file.endsWith('.md')) {
        // index.md는 제외 (VitePress 루트 페이지)
        if (file === 'index.md') continue
        
        // 파일의 상대 경로를 계산
        const relativePath = relative(baseDir, fullPath)
        const link = '/' + relativePath.replace(/\\/g, '/').replace(/\.md$/, '')
        const fileName = parse(file).name
        
        items.push({
          text: formatTitle(fileName),
          link: link
        })
      }
    }
  } catch (error) {
    console.warn(`디렉토리 읽기 실패: ${dir}`, error)
  }
  
  return items
}

// 파일/폴더 이름을 읽기 쉬운 제목으로 변환
function formatTitle(name: string): string {
  return name
    .replace(/-/g, ' ')
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// docs 디렉토리의 절대 경로
const docsDir = join(__dirname, '..')

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "AI Agent",
  description: "AI Agent 학습 문서",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '홈', link: '/' },
      { text: '팀 문서', link: '/team/' },
      { text: 'Maestro', link: '/team/ko/maestro-orchestrator' }
    ],

    // 자동 생성된 사이드바
    sidebar: generateSidebar(docsDir),

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ],
    
    // 검색 활성화
    search: {
      provider: 'local'
    }
  }
})
