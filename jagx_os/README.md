# JagX OS

JagX OS is the planned free, open-source operating-system layer for the JagX project.

## Design

JagX OS will be a bootable Linux-based environment with the JagX assistant, desktop command center, local AI, file/browser automation, privacy controls, and hardware-aware tools integrated into the desktop.

## Switching

A running Windows program cannot safely change the operating system kernel in place. JagX therefore treats OS switching as a **reboot-and-boot-selection** operation. Any future Windows/JagX OS dual-boot manager must be explicit, visible, and confirmation-gated before changing boot configuration.

## Goals

- Free and open-source base
- Offline-first local AI
- JagX dashboard as the primary shell
- Hardware and power controls
- Existing Windows files accessible through normal mounted storage
- Safe boot and recovery path
- Optional dual-boot with Windows
- No hidden bootloader changes

This directory is the foundation for the JagX OS build; it does not modify a user's boot configuration automatically.
