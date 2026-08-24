import type { Metadata, Viewport } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudyUIC",
  description: "Find study spots and live study groups at UIC.",
  applicationName: "StudyUIC",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#001E62",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
