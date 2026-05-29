
USE movie_system;
-- CREATE TABLE `user` (
--     `id` VARCHAR(50) NOT NULL,
--     `full_name` VARCHAR(100),
--     `username` VARCHAR(50),
--     `email` VARCHAR(50),
--     `phone_number` VARCHAR(15),
--     `password` VARCHAR(100),
--     `is_active` TINYINT(1) DEFAULT 1,     -- Boolean trong MySQL là TINYINT
--     `is_verified` TINYINT(1) DEFAULT 0,
--     `is_deleted` TINYINT(1) DEFAULT 0,
--     `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,movie
--     `created_by` VARCHAR(50),
--     `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     `updated_by` VARCHAR(50),
--     PRIMARY KEY (`id`)
-- );

-- -- 2. TẠO BẢNG MOVIE (Cũng đứng độc lập)
-- CREATE TABLE `movie` (
--     `id` VARCHAR(50) NOT NULL,
--     `name` VARCHAR(50),
--     `slug_name` VARCHAR(50),
--     `is_series` TINYINT(1) DEFAULT 0,
--     `description` VARCHAR(1000),
--     `is_deleted` TINYINT(1) DEFAULT 0,
--     `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
--     `created_by` VARCHAR(50),
--     `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     `updated_by` VARCHAR(50),
--     PRIMARY KEY (`id`)
-- );

-- -- 3. TẠO BẢNG COLLECTIONS (Bộ sưu tập - Phụ thuộc vào User)
-- CREATE TABLE `collections` (user
--     `id` VARCHAR(50) NOT NULL,
--     `user_id` VARCHAR(50) NOT NULL,
--     `name` VARCHAR(100) NOT NULL,
--     `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
--     PRIMARY KEY (`id`),
--     -- Ràng buộc khóa ngoại: Xóa User là xóa luôn Collection
--     CONSTRAINT `fk_collection_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
-- );

-- -- 4. TẠO BẢNG COLLECTION_ITEMS (Bảng trung gian Nhiều-Nhiều)
-- CREATE TABLE `collection_items` (
--     `collection_id` VARCHAR(50) NOT NULL,
--     `movie_id` VARCHAR(50) NOT NULL,
--     `added_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
--     
--     -- Khóa chính kép chống duplicate phim trong cùng 1 danh sách
--     PRIMARY KEY (`collection_id`, `movie_id`),
--     
--     -- Xóa Collection thì phim trong list bốc hơi
--     CONSTRAINT `fk_item_collection` FOREIGN KEY (`collection_id`) REFERENCES `collections`(`id`) ON DELETE CASCADE,
--     -- Phim bị gỡ khỏi web thì tự động văng ra khỏi danh sách của mọi User
--     CONSTRAINT `fk_item_movie` FOREIGN KEY (`movie_id`) REFERENCES `movie`(`id`) ON DELETE CASCADE
-- );

-- CREATE TABLE episode (
--     id VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     id_movie VARCHAR(50),
--     link_video VARCHAR(100),
--     name_episode VARCHAR(50),
--     description VARCHAR(100),
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by VARCHAR(50),
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50)
-- );

-- CREATE TABLE `transactions` (
--     `id` VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     `user_id` VARCHAR(50) NOT NULL,
--     `package_id` VARCHAR(50) NOT NULL,
--     `amount` INT NOT NULL,
--     `status` VARCHAR(50) DEFAULT 'PENDING',
--     `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
--     
--     CONSTRAINT `fk_transaction_user`
--         FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
--         
--     CONSTRAINT `fk_transaction_package` 
--         FOREIGN KEY (`package_id`) REFERENCES `subscription_packages`(`id`) ON DELETE CASCADE
-- );

-- CREATE TABLE `shorts` (
--     `id` VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     `movie_id` VARCHAR(50) NOT NULL,
-- 	`episode_id` VARCHAR(50) NOT NULL,
-- 	`user_id` VARCHAR(50) NOT NULL,

--     `title` VARCHAR(1000) NOT NULL,
-- 	`slug` VARCHAR(200),
-- 	`start_time` INTEGER,
-- 	`duration` INTEGER,
--     `video_url` VARCHAR(500) NOT NULL,
--     
--     `like_count` INT DEFAULT(0),
-- 	`view_count` INT DEFAULT(0),

--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by VARCHAR(50),
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50),
--     
--     CONSTRAINT `fk_short_user`
-- 		FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
--         
--     CONSTRAINT `fk_short_movie`
--         FOREIGN KEY (`movie_id`) REFERENCES `movie`(`id`) ON DELETE CASCADE,
--         
--     CONSTRAINT `fk_short_episode` 
--         FOREIGN KEY (`episode_id`) REFERENCES `episode`(`id`) ON DELETE CASCADE
-- );
-- SELECT * FROM subscription_packages;

alter table user add column avatar varchar(100) default null;
select * FROM user;
