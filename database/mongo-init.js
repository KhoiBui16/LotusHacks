const dbName = process.env.MONGODB_DB_NAME || "lotushacks";
const db = db.getSiblingDB(dbName);

db.createCollection("users");
db.createCollection("vehicles");
db.createCollection("claims");
db.createCollection("claim_documents");
db.createCollection("notifications");
db.createCollection("settings");
db.createCollection("uploads");

db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ created_at: -1 });

db.vehicles.createIndex({ user_id: 1, created_at: -1 });
db.vehicles.createIndex({ user_id: 1, plate: 1 });

db.claims.createIndex({ user_id: 1, created_at: -1 });
db.claims.createIndex({ user_id: 1, vehicle_id: 1, created_at: -1 });
db.claims.createIndex({ user_id: 1, status: 1, updated_at: -1 });

db.claim_documents.createIndex({ claim_id: 1, doc_type: 1 }, { unique: true });
db.notifications.createIndex({ user_id: 1, created_at: -1 });
db.notifications.createIndex({ user_id: 1, read: 1, created_at: -1 });
db.settings.createIndex({ user_id: 1 }, { unique: true });
db.uploads.createIndex({ user_id: 1, created_at: -1 });
