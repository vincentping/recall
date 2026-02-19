"""Setup script for initializing exam database structures."""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.db_manager import DBManager


def setup_aplus_structure(db: DBManager):
    """Initialize CompTIA A+ (220-1101/1102) exam structure (modules and lessons)."""
    print("\n--- Initializing CompTIA A+ (220-1101/1102) exam structure ---")

    try:
        core1_id = db.insert_knowledge_module("Core 1 (220-1101)")
        core2_id = db.insert_knowledge_module("Core 2 (220-1102)")
        print(f"Core 1 ID: {core1_id}, Core 2 ID: {core2_id}")
    except Exception as e:
        print(f"Error: Failed to insert knowledge modules: {e}")
        return

    lesson_data = [
        (core1_id, '1.0', 'What Does an IT Specialist Do?', True),
        (core1_id, '1.1', 'The Hero of Problem Solving', False),
        (core1_id, '1.2', 'The Troubleshooting Methodology', False),

        (core1_id, '2.0', 'Installing Motherboards and Connectors', True),
        (core1_id, '2.1', 'Cables and Connectors', False),
        (core1_id, '2.2', 'Motherboards', False),
        (core1_id, '2.3', 'Legacy Cables', False),

        (core1_id, '3.0', 'Installing System Devices', True),
        (core1_id, '3.1', 'Power Supplies and Cooling', False),
        (core1_id, '3.2', 'Storage Devices', False),
        (core1_id, '3.3', 'System Memory', False),
        (core1_id, '3.4', 'CPUs', False),

        (core1_id, '4.0', 'Troubleshooting PC Hardware', True),
        (core1_id, '4.1', 'BIOS and UEFI', False),
        (core1_id, '4.2', 'Power and Disk Issues', False),
        (core1_id, '4.3', 'System and Display Issues', False),

        (core1_id, '5.0', 'Comparing Local Networking Hardware', True),
        (core1_id, '5.1', 'Network Types', False),
        (core1_id, '5.2', 'Networking Hardware', False),
        (core1_id, '5.3', 'Network Cable Types', False),
        (core1_id, '5.4', 'Wireless Networking Types', False),

        (core1_id, '6.0', 'Configuring Network Addressing and Internet Connection', True),
        (core1_id, '6.1', 'Internet Connection Types', False),
        (core1_id, '6.2', 'TCP/IP Concepts', False),
        (core1_id, '6.3', 'Network Communication', False),
        (core1_id, '6.4', 'Network Configuration Concepts', False),

        (core1_id, '7.0', 'Supporting Network Services', True),
        (core1_id, '7.1', 'Networked Host Services', False),
        (core1_id, '7.2', 'Internet and Embedded Appliances', False),
        (core1_id, '7.3', 'Troubleshoot Networks', False),

        (core1_id, '8.0', 'Summarizing Virtualization and Cloud Concepts', True),
        (core1_id, '8.1', 'Client-Side Virtualization', False),
        (core1_id, '8.2', 'Cloud Concepts', False),

        (core1_id, '9.0', 'Supporting Mobile Devices', True),
        (core1_id, '9.1', 'Mobile Devices and Peripherals', False),
        (core1_id, '9.2', 'Mobile Apps and Data', False),
        (core1_id, '9.3', 'Laptop Hardware', False),
        (core1_id, '9.4', 'Troubleshoot Mobile Devices', False),

        (core1_id, '10.0', 'Supporting Print Devices', True),
        (core1_id, '10.1', 'Printers and Multifunction Devices', False),
        (core1_id, '10.2', 'Print Device Maintenance', False),
        (core1_id, '10.3', 'Troubleshoot Print Devices', False),

        (core2_id, '11.0', 'Managing Support Procedures', True),
        (core2_id, '11.1', 'Documentation', False),
        (core2_id, '11.2', 'Professional Communication', False),
        (core2_id, '11.3', 'Types of Operating Systems', False),

        (core2_id, '12.0', 'Configuring Windows', True),
        (core2_id, '12.1', 'Windows User Settings', False),
        (core2_id, '12.2', 'Windows System Settings', False),
        (core2_id, '12.3', 'Install and Configure Applications', False),
        (core2_id, '12.4', 'Cloud-Based Applications', False),

        (core2_id, '13.0', 'Managing Windows', True),
        (core2_id, '13.1', 'Use Management Consoles', False),
        (core2_id, '13.2', 'Command-Line Tools', False),
        (core2_id, '13.3', 'Windows Networking', False),

        (core2_id, '14.0', 'Supporting Windows', True),
        (core2_id, '14.1', 'Troubleshoot Windows Networking', False),
        (core2_id, '14.2', 'Remote Access Technologies', False),
        (core2_id, '14.3', 'Performance and Troubleshooting Tools', False),
        (core2_id, '14.4', 'Troubleshoot Windows OS Problems', False),

        (core2_id, '15.0', 'Securing Windows', True),
        (core2_id, '15.1', 'Logical Security Concepts', False),
        (core2_id, '15.2', 'Windows Security Settings', False),
        (core2_id, '15.3', 'Windows Shares', False),

        (core2_id, '16.0', 'Installing Operating Systems', True),
        (core2_id, '16.1', 'Windows Editions', False),
        (core2_id, '16.2', 'OS Installations and Upgrades', False),

        (core2_id, '17.0', 'Supporting Other OS', True),
        (core2_id, '17.1', 'Linux Features', False),
        (core2_id, '17.2', 'Package and Network Management', False),
        (core2_id, '17.3', 'macOS Features', False),

        (core2_id, '18.0', 'Configuring SOHO Network Security', True),
        (core2_id, '18.1', 'Attacks, Threats, and Vulnerabilities', False),
        (core2_id, '18.2', 'Wireless Security Protocols', False),
        (core2_id, '18.3', 'SOHO Router Security', False),
        (core2_id, '18.4', 'Additional Security Measures', False),

        (core2_id, '19.0', 'Managing Security Settings', True),
        (core2_id, '19.1', 'Account Security', False),
        (core2_id, '19.2', 'Workstation Security', False),
        (core2_id, '19.3', 'Browser Security', False),
        (core2_id, '19.4', 'Troubleshoot Workstation Security', False),

        (core2_id, '20.0', 'Supporting Mobile Software', True),
        (core2_id, '20.1', 'Mobile OS Security', False),
        (core2_id, '20.2', 'Troubleshoot Mobile OS and App Software', False),
        (core2_id, '20.3', 'Troubleshoot Mobile OS and App Security', False),

        (core2_id, '21.0', 'Using Data Security', True),
        (core2_id, '21.1', 'Data Backup and Recovery', False),
        (core2_id, '21.2', 'Data Handling Best Practices', False),
        (core2_id, '21.3', 'Artificial Intelligence', False),

        (core2_id, '22.0', 'Implementing Operational Procedures', True),
        (core2_id, '22.1', 'Change and Inventory Management', False),
        (core2_id, '22.2', 'Common Safety and Environmental Procedures', False),
        (core2_id, '22.3', 'Scripting Basics', False),
    ]

    inserted_count = 0
    for module_id, num, title, is_chapter in lesson_data:
        lesson_id = db.insert_lesson(module_id, num, title, is_chapter)
        if lesson_id:
            inserted_count += 1

    # Store exam name
    db.set_exam_name("CompTIA A+ (220-1101/1102)")

    print(f"Successfully inserted {inserted_count} chapter/lesson records.")
    print("--------------------------------------------------")


def create_template(db_path: str):
    """Create an empty template database with tables only."""
    print(f"\n--- Creating template database: {db_path} ---")
    with DBManager(db_path) as db:
        db.set_exam_name("New Exam")
    print("Template database created successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Setup exam database structures")
    parser.add_argument('--template', type=str, metavar='PATH',
                        help="Create an empty template DB at the given path")
    args = parser.parse_args()

    if args.template:
        create_template(args.template)
    else:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'default.db'
        )
        try:
            with DBManager(db_path) as db:
                setup_aplus_structure(db)
        except Exception as e:
            print(f"Setup failed: {e}")
            sys.exit(1)
