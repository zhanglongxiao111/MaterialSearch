-- ============================================
-- MaterialSearch Supabase Row Level Security
-- 版本: 003
-- 描述: 添加 RLS 策略实现数据隔离
-- ============================================

-- ============================================
-- 启用 RLS
-- ============================================
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dedup_jobs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 辅助函数：获取当前用户角色
-- ============================================
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN (
        SELECT role 
        FROM user_profiles 
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 辅助函数：检查是否为管理员
-- ============================================
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_user_role() = 'admin';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- user_profiles 策略
-- ============================================
-- 用户可以查看所有用户的基本信息
CREATE POLICY "用户可查看所有 profile"
    ON user_profiles FOR SELECT
    TO authenticated
    USING (true);

-- 用户只能更新自己的 profile
CREATE POLICY "用户可更新自己的 profile"
    ON user_profiles FOR UPDATE
    TO authenticated
    USING (id = auth.uid());

-- 管理员可以管理所有用户
CREATE POLICY "管理员可管理所有用户"
    ON user_profiles FOR ALL
    TO authenticated
    USING (is_admin());

-- ============================================
-- projects 策略
-- ============================================
-- 所有登录用户可以查看项目
CREATE POLICY "登录用户可查看项目"
    ON projects FOR SELECT
    TO authenticated
    USING (is_deleted = false OR is_admin());

-- designer 和 admin 可以创建项目
CREATE POLICY "设计师可创建项目"
    ON projects FOR INSERT
    TO authenticated
    WITH CHECK (get_user_role() IN ('admin', 'designer'));

-- designer 可以更新自己创建的项目，admin 可以更新所有
CREATE POLICY "设计师可更新项目"
    ON projects FOR UPDATE
    TO authenticated
    USING (
        owner_id = auth.uid() 
        OR is_admin()
    );

-- 只有管理员可以删除项目
CREATE POLICY "管理员可删除项目"
    ON projects FOR DELETE
    TO authenticated
    USING (is_admin());

-- ============================================
-- images 策略
-- ============================================
-- 所有登录用户可以查看图片
CREATE POLICY "登录用户可查看图片"
    ON images FOR SELECT
    TO authenticated
    USING (is_deleted = false OR is_admin());

-- designer 和 admin 可以添加图片
CREATE POLICY "设计师可添加图片"
    ON images FOR INSERT
    TO authenticated
    WITH CHECK (get_user_role() IN ('admin', 'designer'));

-- designer 可以更新自己上传的图片
CREATE POLICY "设计师可更新图片"
    ON images FOR UPDATE
    TO authenticated
    USING (
        created_by = auth.uid() 
        OR is_admin()
    );

-- 只有管理员可以删除图片
CREATE POLICY "管理员可删除图片"
    ON images FOR DELETE
    TO authenticated
    USING (is_admin());

-- ============================================
-- videos 策略
-- ============================================
-- 所有登录用户可以查看视频
CREATE POLICY "登录用户可查看视频"
    ON videos FOR SELECT
    TO authenticated
    USING (is_deleted = false OR is_admin());

-- designer 和 admin 可以添加视频
CREATE POLICY "设计师可添加视频"
    ON videos FOR INSERT
    TO authenticated
    WITH CHECK (get_user_role() IN ('admin', 'designer'));

-- designer 可以更新自己上传的视频
CREATE POLICY "设计师可更新视频"
    ON videos FOR UPDATE
    TO authenticated
    USING (
        created_by = auth.uid() 
        OR is_admin()
    );

-- 只有管理员可以删除视频
CREATE POLICY "管理员可删除视频"
    ON videos FOR DELETE
    TO authenticated
    USING (is_admin());

-- ============================================
-- audit_logs 策略
-- ============================================
-- 只有管理员可以查看审计日志
CREATE POLICY "管理员可查看审计日志"
    ON audit_logs FOR SELECT
    TO authenticated
    USING (is_admin());

-- 系统可以插入审计日志（通过 service role）
CREATE POLICY "系统可插入审计日志"
    ON audit_logs FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- ============================================
-- dedup_jobs 策略
-- ============================================
-- 登录用户可以查看去重任务
CREATE POLICY "登录用户可查看去重任务"
    ON dedup_jobs FOR SELECT
    TO authenticated
    USING (true);

-- designer 和 admin 可以创建去重任务
CREATE POLICY "设计师可创建去重任务"
    ON dedup_jobs FOR INSERT
    TO authenticated
    WITH CHECK (get_user_role() IN ('admin', 'designer'));

-- 只有创建者或管理员可以更新去重任务
CREATE POLICY "创建者可更新去重任务"
    ON dedup_jobs FOR UPDATE
    TO authenticated
    USING (
        created_by = auth.uid() 
        OR is_admin()
    );

-- ============================================
-- 审计日志触发器
-- ============================================
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
    VALUES (
        auth.uid(),
        TG_OP,
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id::text
            ELSE NEW.id::text
        END,
        CASE 
            WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD)
            ELSE to_jsonb(NEW)
        END
    );
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 为关键表添加审计触发器
CREATE TRIGGER audit_projects_changes
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_images_changes
    AFTER DELETE ON images
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_videos_changes
    AFTER DELETE ON videos
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();
