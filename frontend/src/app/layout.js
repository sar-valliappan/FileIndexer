import './globals.css'

export const metadata = {
  title: 'AI File Search',
  description: 'Semantic search for local files using AI embeddings',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}