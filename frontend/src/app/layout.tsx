import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"
import { Sidebar } from "@/components/layout/sidebar"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "PromptScope — AI Visibility Monitoring",
  description: "Monitor your brand visibility across AI language model providers",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-900 text-slate-100`}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-60 min-h-screen bg-slate-900">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
