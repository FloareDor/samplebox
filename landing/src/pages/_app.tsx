import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { Inter } from 'next/font/google';
import { cn } from '@/lib/utils';

const fontHeading = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-heading',
});

const fontBody = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <main className={cn(
      'antialiased',
      fontHeading.variable,
      fontBody.variable
    )}>
      <Component {...pageProps} />
    </main>
  );
}