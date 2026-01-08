import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "./contexts/AuthContext";
import { RoleProvider } from "./contexts/RoleContext";
import { TenantProvider } from "./contexts/TenantContext";
import AppShell from "@/components/AppShell";

// Import dev auth helper in development
if (process.env.NODE_ENV === "development") {
  import("./lib/dev-auth");
}

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Mem0-RAG Admin UI",
  description: "Admin UI for Mem0-RAG platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <RoleProvider>
            <TenantProvider>
              <AppShell>{children}</AppShell>
            </TenantProvider>
          </RoleProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
