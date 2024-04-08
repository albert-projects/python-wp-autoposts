-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Apr 08, 2024 at 11:06 AM
-- Server version: 10.6.16-MariaDB-0ubuntu0.22.04.1
-- PHP Version: 8.1.2-1ubuntu2.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `AutoNews`
--
CREATE DATABASE IF NOT EXISTS `AutoNews` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `AutoNews`;

-- --------------------------------------------------------

--
-- Table structure for table `Aust-Traveller_experiences`
--

CREATE TABLE `Aust-Traveller_experiences` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_url` text DEFAULT NULL,
  `type` text DEFAULT NULL,
  `state` text DEFAULT NULL,
  `area` text DEFAULT NULL,
  `city` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `linkUrl` text DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Aust-Traveller_translated`
--

CREATE TABLE `Aust-Traveller_translated` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_url` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `com_header` text DEFAULT NULL,
  `ori_content` text DEFAULT NULL,
  `chi_content` text DEFAULT NULL,
  `cn_content` text DEFAULT NULL,
  `en_content` text DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_finance`
--

CREATE TABLE `SBS_australian_finance` (
  `id` int(11) NOT NULL,
  `page_time` datetime NOT NULL DEFAULT current_timestamp(),
  `html_content` mediumtext DEFAULT NULL,
  `remark` char(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_finance_items`
--

CREATE TABLE `SBS_australian_finance_items` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_id` int(11) NOT NULL,
  `id` text DEFAULT NULL,
  `type` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `linkUrl` text DEFAULT NULL,
  `permalink` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_immigration`
--

CREATE TABLE `SBS_australian_immigration` (
  `id` int(11) NOT NULL,
  `page_time` datetime NOT NULL DEFAULT current_timestamp(),
  `html_content` mediumtext DEFAULT NULL,
  `remark` char(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_immigration_items`
--

CREATE TABLE `SBS_australian_immigration_items` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_id` int(11) NOT NULL,
  `id` text DEFAULT NULL,
  `type` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `linkUrl` text DEFAULT NULL,
  `permalink` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_living`
--

CREATE TABLE `SBS_australian_living` (
  `id` int(11) NOT NULL,
  `page_time` datetime NOT NULL DEFAULT current_timestamp(),
  `html_content` mediumtext DEFAULT NULL,
  `remark` char(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_living_items`
--

CREATE TABLE `SBS_australian_living_items` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_id` int(11) NOT NULL,
  `id` text DEFAULT NULL,
  `type` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `linkUrl` text DEFAULT NULL,
  `permalink` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_news`
--

CREATE TABLE `SBS_australian_news` (
  `id` int(11) NOT NULL,
  `page_time` datetime NOT NULL DEFAULT current_timestamp(),
  `html_content` mediumtext DEFAULT NULL,
  `remark` char(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SBS_australian_news_items`
--

CREATE TABLE `SBS_australian_news_items` (
  `idx` int(11) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT current_timestamp(),
  `ref_id` int(11) NOT NULL,
  `id` text DEFAULT NULL,
  `type` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `linkUrl` text DEFAULT NULL,
  `permalink` text DEFAULT NULL,
  `published` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Aust-Traveller_experiences`
--
ALTER TABLE `Aust-Traveller_experiences`
  ADD PRIMARY KEY (`idx`);

--
-- Indexes for table `Aust-Traveller_translated`
--
ALTER TABLE `Aust-Traveller_translated`
  ADD PRIMARY KEY (`idx`);

--
-- Indexes for table `SBS_australian_finance`
--
ALTER TABLE `SBS_australian_finance`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `SBS_australian_finance_items`
--
ALTER TABLE `SBS_australian_finance_items`
  ADD PRIMARY KEY (`idx`);

--
-- Indexes for table `SBS_australian_immigration`
--
ALTER TABLE `SBS_australian_immigration`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `SBS_australian_immigration_items`
--
ALTER TABLE `SBS_australian_immigration_items`
  ADD PRIMARY KEY (`idx`);

--
-- Indexes for table `SBS_australian_living`
--
ALTER TABLE `SBS_australian_living`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `SBS_australian_living_items`
--
ALTER TABLE `SBS_australian_living_items`
  ADD PRIMARY KEY (`idx`);

--
-- Indexes for table `SBS_australian_news`
--
ALTER TABLE `SBS_australian_news`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `SBS_australian_news_items`
--
ALTER TABLE `SBS_australian_news_items`
  ADD PRIMARY KEY (`idx`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Aust-Traveller_experiences`
--
ALTER TABLE `Aust-Traveller_experiences`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Aust-Traveller_translated`
--
ALTER TABLE `Aust-Traveller_translated`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_finance`
--
ALTER TABLE `SBS_australian_finance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_finance_items`
--
ALTER TABLE `SBS_australian_finance_items`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_immigration`
--
ALTER TABLE `SBS_australian_immigration`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_immigration_items`
--
ALTER TABLE `SBS_australian_immigration_items`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_living`
--
ALTER TABLE `SBS_australian_living`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_living_items`
--
ALTER TABLE `SBS_australian_living_items`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_news`
--
ALTER TABLE `SBS_australian_news`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SBS_australian_news_items`
--
ALTER TABLE `SBS_australian_news_items`
  MODIFY `idx` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
