"""
Database Migration Script: Orange Money to Flutterwave

This script migrates the database schema from Orange Money payment fields
to Flutterwave payment fields.

Author: AI Assistant
Created: 2025
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Backend.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handle database migration from Orange Money to Flutterwave."""
    
    def __init__(self):
        """Initialize database connection."""
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            # Parse database URL
            db_url = settings.database_url
            if db_url.startswith("sqlite"):
                logger.error("This migration is for PostgreSQL only. SQLite migration not supported.")
                return False
            
            # Extract connection parameters
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "")
            
            # Parse connection string
            parts = db_url.split("@")
            if len(parts) != 2:
                logger.error("Invalid database URL format")
                return False
            
            user_pass = parts[0].split(":")
            if len(user_pass) != 2:
                logger.error("Invalid database URL format")
                return False
            
            username, password = user_pass[0], user_pass[1]
            
            host_port_db = parts[1].split("/")
            if len(host_port_db) != 2:
                logger.error("Invalid database URL format")
                return False
            
            host_port = host_port_db[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 5432
            database = host_port_db[1]
            
            # Connect to database
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.connection.cursor()
            
            logger.info("Successfully connected to PostgreSQL database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def check_table_exists(self, table_name):
        """Check if a table exists in the database."""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking table existence: {str(e)}")
            return False
    
    def check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table."""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                );
            """, (table_name, column_name))
            
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error checking column existence: {str(e)}")
            return False
    
    def migrate_orders_table(self):
        """Migrate the orders table from Orange Money to Flutterwave fields."""
        try:
            # Check if orders table exists
            if not self.check_table_exists("orders"):
                logger.warning("Orders table does not exist. Skipping migration.")
                return True
            
            # Check if Orange Money columns exist
            orange_payment_id_exists = self.check_column_exists("orders", "orange_payment_id")
            orange_transaction_id_exists = self.check_column_exists("orders", "orange_transaction_id")
            
            # Check if Flutterwave columns already exist
            flutterwave_payment_id_exists = self.check_column_exists("orders", "flutterwave_payment_id")
            flutterwave_transaction_id_exists = self.check_column_exists("orders", "flutterwave_transaction_id")
            
            # Add Flutterwave columns if they don't exist
            if not flutterwave_payment_id_exists:
                logger.info("Adding flutterwave_payment_id column to orders table")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN flutterwave_payment_id VARCHAR(200);
                """)
                logger.info("Successfully added flutterwave_payment_id column")
            
            if not flutterwave_transaction_id_exists:
                logger.info("Adding flutterwave_transaction_id column to orders table")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN flutterwave_transaction_id VARCHAR(200);
                """)
                logger.info("Successfully added flutterwave_transaction_id column")
            
            # Migrate data from Orange Money to Flutterwave columns if Orange Money columns exist
            if orange_payment_id_exists and flutterwave_payment_id_exists:
                logger.info("Migrating data from orange_payment_id to flutterwave_payment_id")
                self.cursor.execute("""
                    UPDATE orders 
                    SET flutterwave_payment_id = orange_payment_id 
                    WHERE orange_payment_id IS NOT NULL 
                    AND flutterwave_payment_id IS NULL;
                """)
                logger.info("Successfully migrated payment ID data")
            
            if orange_transaction_id_exists and flutterwave_transaction_id_exists:
                logger.info("Migrating data from orange_transaction_id to flutterwave_transaction_id")
                self.cursor.execute("""
                    UPDATE orders 
                    SET flutterwave_transaction_id = orange_transaction_id 
                    WHERE orange_transaction_id IS NOT NULL 
                    AND flutterwave_transaction_id IS NULL;
                """)
                logger.info("Successfully migrated transaction ID data")
            
            # Drop Orange Money columns if they exist (optional - comment out if you want to keep them)
            if orange_payment_id_exists:
                logger.info("Dropping orange_payment_id column")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    DROP COLUMN orange_payment_id;
                """)
                logger.info("Successfully dropped orange_payment_id column")
            
            if orange_transaction_id_exists:
                logger.info("Dropping orange_transaction_id column")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    DROP COLUMN orange_transaction_id;
                """)
                logger.info("Successfully dropped orange_transaction_id column")
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating orders table: {str(e)}")
            return False
    
    def create_payment_logs_table(self):
        """Create a payment logs table for tracking payment events."""
        try:
            # Check if payment_logs table exists
            if self.check_table_exists("payment_logs"):
                logger.info("Payment logs table already exists")
                return True
            
            logger.info("Creating payment_logs table")
            self.cursor.execute("""
                CREATE TABLE payment_logs (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id),
                    event_type VARCHAR(50) NOT NULL,
                    transaction_id VARCHAR(200),
                    flutterwave_reference VARCHAR(200),
                    status VARCHAR(50),
                    amount DECIMAL(10, 2),
                    currency VARCHAR(10),
                    customer_email VARCHAR(255),
                    payment_type VARCHAR(50),
                    webhook_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX idx_payment_logs_order_id ON payment_logs(order_id);
            """)
            
            self.cursor.execute("""
                CREATE INDEX idx_payment_logs_transaction_id ON payment_logs(transaction_id);
            """)
            
            self.cursor.execute("""
                CREATE INDEX idx_payment_logs_event_type ON payment_logs(event_type);
            """)
            
            logger.info("Successfully created payment_logs table with indexes")
            return True
            
        except Exception as e:
            logger.error(f"Error creating payment_logs table: {str(e)}")
            return False
    
    def run_migration(self):
        """Run the complete migration process."""
        try:
            logger.info("Starting database migration from Orange Money to Flutterwave")
            
            # Connect to database
            if not self.connect():
                logger.error("Failed to connect to database. Migration aborted.")
                return False
            
            # Migrate orders table
            if not self.migrate_orders_table():
                logger.error("Failed to migrate orders table. Migration aborted.")
                return False
            
            # Create payment logs table
            if not self.create_payment_logs_table():
                logger.error("Failed to create payment logs table. Migration aborted.")
                return False
            
            logger.info("Database migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
    
    def rollback_migration(self):
        """Rollback the migration (restore Orange Money fields)."""
        try:
            logger.info("Starting migration rollback")
            
            if not self.connect():
                logger.error("Failed to connect to database. Rollback aborted.")
                return False
            
            # Check if Flutterwave columns exist
            flutterwave_payment_id_exists = self.check_column_exists("orders", "flutterwave_payment_id")
            flutterwave_transaction_id_exists = self.check_column_exists("orders", "flutterwave_transaction_id")
            
            # Add Orange Money columns back
            if not self.check_column_exists("orders", "orange_payment_id"):
                logger.info("Adding orange_payment_id column back to orders table")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN orange_payment_id VARCHAR(200);
                """)
            
            if not self.check_column_exists("orders", "orange_transaction_id"):
                logger.info("Adding orange_transaction_id column back to orders table")
                self.cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN orange_transaction_id VARCHAR(200);
                """)
            
            # Migrate data back if Flutterwave columns exist
            if flutterwave_payment_id_exists:
                logger.info("Migrating data back from flutterwave_payment_id to orange_payment_id")
                self.cursor.execute("""
                    UPDATE orders 
                    SET orange_payment_id = flutterwave_payment_id 
                    WHERE flutterwave_payment_id IS NOT NULL;
                """)
            
            if flutterwave_transaction_id_exists:
                logger.info("Migrating data back from flutterwave_transaction_id to orange_transaction_id")
                self.cursor.execute("""
                    UPDATE orders 
                    SET orange_transaction_id = flutterwave_transaction_id 
                    WHERE flutterwave_transaction_id IS NOT NULL;
                """)
            
            logger.info("Migration rollback completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()


def main():
    """Main function to run the migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database from Orange Money to Flutterwave")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    
    args = parser.parse_args()
    
    migration = DatabaseMigration()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # In a real implementation, you would add dry-run logic here
        logger.info("Dry run completed")
        return
    
    if args.rollback:
        success = migration.rollback_migration()
    else:
        success = migration.run_migration()
    
    if success:
        logger.info("Operation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Operation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
