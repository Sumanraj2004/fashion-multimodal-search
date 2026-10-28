import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Common Thread — Fashion Search",
  description: "Explore a research collection with text and image search.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">{children}</div>
        <footer className="mx-auto max-w-7xl px-5 pb-8 pt-4 text-center text-xs leading-relaxed text-ink/50">
          Demo built on a public research dataset (Amazon Reviews 2023) sample of ~5k products; not affiliated with Amazon.
        </footer>
      </body>
    </html>
  );
}
