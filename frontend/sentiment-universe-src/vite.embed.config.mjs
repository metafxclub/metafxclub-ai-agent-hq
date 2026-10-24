import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base:'/frontend/public/sentiment-universe/',
  plugins:[react()],
  build:{
    outDir:'dist/hq-embed',emptyOutDir:true,assetsInlineLimit:0,
    // File-backed fonts comply with HQ's default-src 'self' CSP (no data: fonts).
    rollupOptions:{input:'src/embed.jsx',preserveEntrySignatures:'strict',output:{format:'es',entryFileNames:'sentiment-universe.js',inlineDynamicImports:true}},
  },
});
