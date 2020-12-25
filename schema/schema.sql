DROP DATABASE IF EXISTS test_mysql;
CREATE DATABASE test_mysql;
GRANT ALL ON test_mysql.* to 'test'@'%';
USE test_mysql;

DROP TABLE IF EXISTS `test`;

CREATE TABLE IF NOT EXISTS `test` (
	`id` INT NOT NULL AUTO_INCREMENT,
    `a_dec` DECIMAL(10,4) NULL,
	`b_tin` TINYINT NULL,
	`b_sma` SMALLINT NULL,
	`b_med` MEDIUMINT NULL,
	`b_int` INT NULL,
	`b_big` BIGINT NULL,
    `c_flo` FLOAT NULL,
    `d_dou` DOUBLE  NULL,
    `e_bit` BIT(5) NULL,
    `f_dtm` DATETIME NULL,
    `f_dtf` DATETIME(6) NULL,
    `f_tms` TIMESTAMP(6) NULL,
    `f_dat` DATE NULL,
    `f_tim` TIME NULL,
    `f_yea` YEAR NULL,
    `g_cha` CHAR(10) NULL,
    `g_vch` VARCHAR(100) NULL,
    `g_bin` BINARY(10) NULL,
    `g_vbi` VARBINARY(10) NULL,
    `g_tbl` TINYBLOB NULL,
    `g_blo` BLOB NULL,
    `g_mbl` MEDIUMBLOB NULL,
    `g_lbl` LONGBLOB NULL,
    `g_tte` TINYTEXT NULL,
    `g_tex` TEXT NULL,
    `g_mte` MEDIUMTEXT NULL,
    `g_lte` LONGTEXT NULL,
    `g_enu` ENUM('one', 'two', 'three') NULL,
    `g_set` SET('one', 'two', 'three') NULL,
    `h_jso` JSON NULL,
	PRIMARY KEY(`id`)
) ENGINE=InnoDB CHARACTER SET utf8;
