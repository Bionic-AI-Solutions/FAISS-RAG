"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface BreadcrumbItem {
  label: string;
  href: string;
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  
  // Generate breadcrumbs from pathname
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (!pathname) return [{ label: "Home", href: "/" }];
    
    const segments = pathname.split("/").filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [{ label: "Home", href: "/" }];
    
    let currentPath = "";
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const label = segment
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
      breadcrumbs.push({ label, href: currentPath });
    });
    
    return breadcrumbs;
  };
  
  const breadcrumbs = generateBreadcrumbs();
  
  return (
    <nav className="mb-4">
      <ol className="flex items-center gap-2 text-sm">
        {breadcrumbs.map((item, index) => (
          <li key={item.href} className="flex items-center gap-2">
            {index > 0 && <span style={{ color: 'var(--color-text-secondary)' }}>/</span>}
            {index === breadcrumbs.length - 1 ? (
              <span style={{ color: 'var(--color-text-primary)' }}>{item.label}</span>
            ) : (
              <Link
                href={item.href}
                className="hover:underline"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
