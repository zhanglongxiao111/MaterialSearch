-- ============================================
-- MaterialSearch Supabase 初始 Schema
-- 版本: 001
-- 描述: 创建核心表结构
-- ============================================

-- 启用必要扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 用户表（由 Supabase Auth 管理，这里只存储额外信息）
-- ============================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    role TEXT DEFAULT 'designer' CHECK (role IN ('admin', 'designer', 'viewer')),
    department TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- ============================================
-- 项目表
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,  -- proj_2025_万科_01 格式
    name TEXT NOT NULL,
    client_name TEXT,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    image_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    owner_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);

-- ============================================
-- 图片表（永久库）
-- ============================================
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    path TEXT NOT NULL,
    modify_time TIMESTAMPTZ,
    checksum TEXT,
    
    -- 文件属性
    width INTEGER,
    height INTEGER,
    aspect_ratio REAL,
    aspect_ratio_standard TEXT,
    file_size BIGINT,
    file_format TEXT,
    
    -- 时间戳
    upload_time TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ,
    
    -- 分类标签
    category TEXT,
    sub_category TEXT,
    tags JSONB DEFAULT '[]',
    building_type TEXT,
    design_style TEXT,
    
    -- 来源信息
    source_type TEXT DEFAULT 'local',
    source_project TEXT,
    source_notes TEXT,
    
    -- 质量管理
    quality_score REAL,
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- 去重
    phash TEXT,
    duplicate_group TEXT,
    master_image_id INTEGER,
    duplicate_type TEXT,
    duplicate_confidence REAL,
    is_duplicate BOOLEAN DEFAULT FALSE,
    
    -- AI 增强
    ai_description TEXT,
    
    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    
    -- 创建者
    created_by UUID REFERENCES auth.users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_images_path ON images(path);
CREATE INDEX IF NOT EXISTS idx_images_checksum ON images(checksum);
CREATE INDEX IF NOT EXISTS idx_images_category ON images(category);
CREATE INDEX IF NOT EXISTS idx_images_design_style ON images(design_style);
CREATE INDEX IF NOT EXISTS idx_images_is_deleted ON images(is_deleted);
CREATE INDEX IF NOT EXISTS idx_images_phash ON images(phash);

-- ============================================
-- 视频表（永久库）
-- ============================================
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    path TEXT NOT NULL,
    frame_time INTEGER,  -- 帧时间（秒）
    modify_time TIMESTAMPTZ,
    checksum TEXT,
    
    -- 文件属性
    width INTEGER,
    height INTEGER,
    aspect_ratio REAL,
    duration INTEGER,
    file_size BIGINT,
    file_format TEXT,
    
    -- 时间戳
    upload_time TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ,
    
    -- 分类标签
    category TEXT,
    sub_category TEXT,
    tags JSONB DEFAULT '[]',
    building_type TEXT,
    design_style TEXT,
    
    -- 来源信息
    source_type TEXT DEFAULT 'local',
    source_project TEXT,
    source_notes TEXT,
    
    -- 质量管理
    quality_score REAL,
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- AI 增强
    ai_description TEXT,
    
    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    
    -- 创建者
    created_by UUID REFERENCES auth.users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_videos_path ON videos(path);
CREATE INDEX IF NOT EXISTS idx_videos_frame_time ON videos(frame_time);
CREATE INDEX IF NOT EXISTS idx_videos_is_deleted ON videos(is_deleted);

-- ============================================
-- 审计日志表
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- ============================================
-- 去重任务表
-- ============================================
CREATE TABLE IF NOT EXISTS dedup_jobs (
    id TEXT PRIMARY KEY,
    library_type TEXT DEFAULT 'permanent',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    current_phase TEXT,
    progress_percent REAL DEFAULT 0,
    total_duplicates INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- 统计
    total_scanned INTEGER DEFAULT 0,
    duplicate_groups INTEGER DEFAULT 0,
    duplicates_marked INTEGER DEFAULT 0,
    space_saving BIGINT DEFAULT 0,
    
    -- 报告
    report JSONB,
    notes TEXT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_by UUID REFERENCES auth.users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dedup_jobs_status ON dedup_jobs(status);
CREATE INDEX IF NOT EXISTS idx_dedup_jobs_created ON dedup_jobs(created_at DESC);

-- ============================================
-- 更新时间触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用触发器
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_dedup_jobs_updated_at
    BEFORE UPDATE ON dedup_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
