/**
 * Các loại (types) và giao diện (interfaces) dùng chung cho toàn bộ dự án.
 */

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

export interface ProjectMetadata {
  title: string;
  description: string;
  version: string;
}
