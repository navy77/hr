db = db.getSiblingDB("hr_db");  // สร้างและเลือก database

db.div_user.insertOne({
  div_name: "hr",
  password: "hr",
  created_at: new Date()
});
