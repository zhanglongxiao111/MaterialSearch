-- ============================================
-- MaterialSearch Supabase pgvector 支持
-- 版本: 002
-- 描述: 添加向量搜索功能
-- ============================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 为图片表添加向量列
-- ============================================
ALTER TABLE images ADD COLUMN IF NOT EXISTS features vector(512);

-- 创建向量索引（使用 IVFFlat，适合中等规模数据）
-- 注意：需要先有一定量的数据才能创建索引
-- CREATE INDEX IF NOT EXISTS idx_images_features ON images 
--     USING ivfflat (features vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 为视频表添加向量列
-- ============================================
ALTER TABLE videos ADD COLUMN IF NOT EXISTS features vector(512);

-- ============================================
-- 图片向量搜索函数
-- ============================================
CREATE OR REPLACE FUNCTION search_images_by_vector(
    query_vector vector(512),
    similarity_threshold float DEFAULT 0.3,
    result_limit int DEFAULT 100,
    include_deleted boolean DEFAULT false
)
RETURNS TABLE (
    id int,
    path text,
    similarity float,
    category text,
    design_style text,
    width int,
    height int
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.path,
        1 - (i.features <=> query_vector) AS similarity,
        i.category,
        i.design_style,
        i.width,
        i.height
    FROM images i
    WHERE 
        i.features IS NOT NULL
        AND (include_deleted OR i.is_deleted = false)
        AND 1 - (i.features <=> query_vector) >= similarity_threshold
    ORDER BY i.features <=> query_vector
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 视频向量搜索函数
-- ============================================
CREATE OR REPLACE FUNCTION search_videos_by_vector(
    query_vector vector(512),
    similarity_threshold float DEFAULT 0.3,
    result_limit int DEFAULT 100,
    include_deleted boolean DEFAULT false
)
RETURNS TABLE (
    id int,
    path text,
    frame_time int,
    similarity float,
    duration int
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.path,
        v.frame_time,
        1 - (v.features <=> query_vector) AS similarity,
        v.duration
    FROM videos v
    WHERE 
        v.features IS NOT NULL
        AND (include_deleted OR v.is_deleted = false)
        AND 1 - (v.features <=> query_vector) >= similarity_threshold
    ORDER BY v.features <=> query_vector
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 批量插入向量函数（用于数据迁移）
-- ============================================
CREATE OR REPLACE FUNCTION upsert_image_with_vector(
    p_path text,
    p_features float[],
    p_checksum text DEFAULT NULL,
    p_width int DEFAULT NULL,
    p_height int DEFAULT NULL,
    p_file_size bigint DEFAULT NULL
)
RETURNS int AS $$
DECLARE
    result_id int;
BEGIN
    INSERT INTO images (path, features, checksum, width, height, file_size)
    VALUES (p_path, p_features::vector(512), p_checksum, p_width, p_height, p_file_size)
    ON CONFLICT (path) 
    DO UPDATE SET 
        features = p_features::vector(512),
        checksum = COALESCE(p_checksum, images.checksum),
        updated_at = NOW()
    RETURNING id INTO result_id;
    
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 相似图片查找函数（用于去重）
-- ============================================
CREATE OR REPLACE FUNCTION find_similar_images(
    target_id int,
    similarity_threshold float DEFAULT 0.95,
    result_limit int DEFAULT 10
)
RETURNS TABLE (
    id int,
    path text,
    similarity float
) AS $$
DECLARE
    target_vector vector(512);
BEGIN
    -- 获取目标图片的向量
    SELECT features INTO target_vector 
    FROM images 
    WHERE images.id = target_id;
    
    IF target_vector IS NULL THEN
        RETURN;
    END IF;
    
    RETURN QUERY
    SELECT 
        i.id,
        i.path,
        1 - (i.features <=> target_vector) AS similarity
    FROM images i
    WHERE 
        i.id != target_id
        AND i.features IS NOT NULL
        AND i.is_deleted = false
        AND 1 - (i.features <=> target_vector) >= similarity_threshold
    ORDER BY i.features <=> target_vector
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 统计函数
-- ============================================
CREATE OR REPLACE FUNCTION get_library_stats()
RETURNS TABLE (
    total_images bigint,
    total_videos bigint,
    total_size bigint,
    indexed_images bigint,
    indexed_videos bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM images WHERE is_deleted = false),
        (SELECT COUNT(*) FROM videos WHERE is_deleted = false),
        (SELECT COALESCE(SUM(file_size), 0) FROM images WHERE is_deleted = false) +
        (SELECT COALESCE(SUM(file_size), 0) FROM videos WHERE is_deleted = false),
        (SELECT COUNT(*) FROM images WHERE is_deleted = false AND features IS NOT NULL),
        (SELECT COUNT(*) FROM videos WHERE is_deleted = false AND features IS NOT NULL);
END;
$$ LANGUAGE plpgsql;
