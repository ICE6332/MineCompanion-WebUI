#!/usr/bin/env node
'use strict';

const { spawn } = require('child_process');
const path = require('path');
const treeKill = require('tree-kill');

const backendEntry = path.join(__dirname, '..', 'main.py').replace(/\\/g, '/');

console.log(`使用 uv run python 启动后端服务（入口: ${backendEntry}）。`);

const child = spawn('uv', ['run', 'python', backendEntry], {
  stdio: 'inherit',
  shell: false,
  cwd: path.join(__dirname, '..'),
  detached: false,
});

// 记录子进程 PID 便于调试
child.on('spawn', () => {
  console.log(`后端进程已启动 (PID: ${child.pid})`);
});

// 退出时确保后端子进程被杀掉，避免端口悬挂
let isCleaning = false;

const cleanup = (code, signal, fromExitEvent = false) => {
  if (isCleaning) return;
  isCleaning = true;

  if (child && child.pid && !child.killed) {
    console.log(`正在清理后端进程树 (PID: ${child.pid})...`);

    try {
      // 先礼貌请求：SIGTERM（给应用保存状态的机会）
      treeKill(child.pid, 'SIGTERM', (err) => {
        if (err) {
          console.warn(`SIGTERM 清理失败: ${err.message}`);
        }
      });

      // 2秒后强制清理：SIGKILL（确保进程树被彻底杀死）
      setTimeout(() => {
        if (!child.killed) {
          treeKill(child.pid, 'SIGKILL', (err) => {
            if (err) {
              console.error(`SIGKILL 强制清理失败: ${err.message}`);
            } else {
              console.log('后端进程树已强制清理');
            }
          });
        }
      }, 2000);
    } catch (err) {
      console.error(`停止后端进程失败: ${err.message}`);
    }
  }

  // 让并发脚本能感知退出码/信号
  if (fromExitEvent) return;
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
};

process.on('SIGINT', () => cleanup(0, null));
process.on('SIGTERM', () => cleanup(0, null));
process.on('exit', (code) => cleanup(code, null, true));
process.on('uncaughtException', (err) => {
  console.error(`后端启动器异常：${err.message}`);
  cleanup(1, null);
});

child.once('error', (error) => {
  console.error(`启动后端失败: ${error.message}`);
  console.error('请确认已安装 uv: https://github.com/astral-sh/uv');
  process.exit(1);
});

child.once('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
