#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

console.log('🚀 Installing SaaS MVP Launcher...\n');

// Get npm global bin directory
try {
  const globalBin = execSync('npm bin -g', { encoding: 'utf-8' }).trim();
  const cliSource = path.join(__dirname, 'bin', 'saas-mvp-launcher.mjs');
  const cliTarget = path.join(globalBin, 'saas-mvp-launcher.mjs');
  const cmdTarget = path.join(globalBin, 'saas-mvp-launcher.cmd');
  
  // Copy CLI
  fs.copyFileSync(cliSource, cliTarget);
  
  // Create Windows batch file
  const batchContent = `@echo off\nnode "${cliTarget}" %*`;
  fs.writeFileSync(cmdTarget, batchContent);
  
  console.log('✅ SaaS MVP Launcher installed globally!');
  console.log('\nUsage:');
  console.log('  saas-mvp-launcher create my-app --template fullstack');
  console.log('  saas-mvp-launcher list-templates');
  console.log('  saas-mvp-launcher deploy ./my-app --target docker');
  console.log('');
} catch (e) {
  console.error('❌ Installation failed:', e.message);
  console.log('\nTry running with administrator privileges.');
  process.exit(1);
}
