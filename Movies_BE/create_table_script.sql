
-- USE movie_system;
-- CREATE TABLE favourite_list (
--     id VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     user_id VARCHAR(50),
--     movie_id VARCHAR(50),
--     name_list VARCHAR(100),
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by VARCHAR(50),
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50)
-- );

-- CREATE TABLE user (
--     id VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     name VARCHAR(50),
--     email VARCHAR(50),
--     password VARCHAR(100),
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by VARCHAR(50),
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50)
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

-- CREATE TABLE movie (
--     id VARCHAR(50) PRIMARY KEY DEFAULT(UUID()),
--     slug_name VARCHAR(50),
--     is_series BOOLEAN,
--     description VARCHAR(100),
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     created_by VARCHAR(50),
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50)
-- );

use movie_system;
-- set SQL_SAFE_UPDATES =0;
-- delete from movieepisode
select * from movie;
-- select * from episode;

-- select * from episode;
-- Thêm cột is_deleted vào bảng movie
-- ALTER TABLE movie ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;

-- Thêm cột is_deleted vào bảng episode (nếu bạn có làm cho episode)
-- ALTER TABLE episode ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;