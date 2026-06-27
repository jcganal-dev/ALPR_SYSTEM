-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 11, 2026 at 07:35 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `license_plate_recognition_system`
--

-- --------------------------------------------------------

--
-- Table structure for table `registration_table`
--

CREATE TABLE `registration_table` (
  `registration_id` int(11) NOT NULL,
  `plate_number` varchar(15) NOT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `sticker_number` varchar(20) DEFAULT NULL,
  `or_cr` int(11) DEFAULT NULL,
  `vehicle_type` varchar(20) NOT NULL,
  `body_number` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `registration_table`
--

INSERT INTO `registration_table` (`registration_id`, `plate_number`, `last_name`, `first_name`, `sticker_number`, `or_cr`, `vehicle_type`, `body_number`) VALUES
(1, 'ABC1234', 'DOE', 'JOHN', 'STK-001', 123456, 'TOYOTA VIOS', 'B-01'),
(2, 'XYZ9876', 'SMITH', 'JANE', 'STK-002', 654321, 'HONDA CIVIC', 'B-02'),
(3, 'LMN4567', 'DELA CRUZ', 'JUAN', 'STK-003', 112233, 'FORD RANGER', 'B-03'),
(4, 'QWE3210', 'WAYNE', 'BRUCE', 'STK-004', 998877, 'MITSUBISHI MONTERO', 'B-04'),
(5, 'RTY6543', 'KENT', 'CLARK', 'STK-005', 445566, 'YAMAHA NMAX', 'B-05'),
(6, 'DFG7890', 'PRINCE', 'DIANA', 'STK-006', 778899, 'SUZUKI RAIDER', 'B-06'),
(7, 'CVB0987', 'ALLEN', 'BARRY', 'STK-007', 332211, 'HONDA CLICK', 'B-07'),
(8, 'GHJ5678', 'STARK', 'TONY', 'STK-008', 556677, 'NISSAN NAVARA', 'B-08'),
(9, 'TYU4321', 'BANNER', 'BRUCE', 'STK-009', 223344, 'ISUZU DMAX', 'B-09'),
(10, 'ZXC1357', 'PARKER', 'PETER', 'STK-010', 889900, 'TOYOTA INNOVA', 'B-10');

-- --------------------------------------------------------

--
-- Indexes for dumped tables
--

--
-- Indexes for table `registration_table`
--
ALTER TABLE `registration_table`
  ADD PRIMARY KEY (`registration_id`),
  ADD UNIQUE KEY `plate_number` (`plate_number`),
  ADD UNIQUE KEY `sticker_number` (`sticker_number`);

--
-- Indexes for table `transaction_table`
--
ALTER TABLE `transaction_table`
  ADD PRIMARY KEY (`transaction_id`) USING BTREE;

--
-- Indexes for table `unregistered_plates`
--
ALTER TABLE `unregistered_plates`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `plate_number` (`plate_number`),
  ADD KEY `ix_unregistered_plates_id` (`id`);

--
-- Indexes for table `user_table`
--
ALTER TABLE `user_table`
  ADD UNIQUE KEY `employee_id` (`employee_id`);

--
-- Indexes for table `watchlist_table`
--
ALTER TABLE `watchlist_table`
  ADD UNIQUE KEY `plate_number` (`plate_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `registration_table`
--
ALTER TABLE `registration_table`
  MODIFY `registration_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `unregistered_plates`
--
ALTER TABLE `unregistered_plates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;