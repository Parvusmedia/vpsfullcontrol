import type { Metadata } from "next";
import "../src/app.css";

export const metadata: Metadata = {
  title: "Digitanimal · Google Ads",
  robots: { index: false },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
