const dbName = process.env.MONGODB_DB_NAME || "lotushacks";
const db = db.getSiblingDB(dbName);

db.createCollection("users");

db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ createdAt: -1 });

