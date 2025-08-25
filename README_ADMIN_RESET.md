# 🛠️ Admin Reset Commands

The casino bot now includes comprehensive admin reset commands that allow administrators to reset various user data. These commands are **administrator-only** and provide full control over user accounts.

## 🔐 **Administrator Access Required**

All reset commands require administrator privileges. Only users listed in the `Admins` sheet can use these commands.

## 📋 **Available Reset Commands**

### **1. 🔄 `/resetall <username_or_id>`**
**Complete user reset - resets everything to starting state**

**What it resets:**
- Balance → 1,000 coins (starting balance)
- XP → 0
- Level → 1
- Total Bets → 0
- Daily Streak → 0
- All Milestones → False
- Active Loans → Cleared
- Betting Logs → Cleared

**Usage Examples:**
```
/resetall @username
/resetall 123456789
/resetall username123
```

**Example Output:**
```
🔄 Complete Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
📊 Reset Fields:
  • Balance → 1,000 coins
  • XP → 0
  • Level → 1
  • Total Bets → 0
  • Daily Streak → 0
  • All Milestones → False
  • Active Loans → Cleared
  • Betting Logs → Cleared

✅ User has been completely reset to starting state!
```

---

### **2. 💰 `/resetbalance <username_or_id> [amount]`**
**Reset user balance to specified amount (default: 1,000 coins)**

**What it resets:**
- Balance → Specified amount (or 1,000 if not specified)

**Usage Examples:**
```
/resetbalance @username
/resetbalance 123456789 5000
/resetbalance username123 10000
```

**Example Output:**
```
💰 Balance Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
💵 Old Balance: 25,000 coins
🔄 New Balance: 5,000 coins

✅ Balance has been reset!
```

---

### **3. ⭐ `/resetxp <username_or_id> [xp] [level]`**
**Reset user XP and level (default: 0 XP, level 1)**

**What it resets:**
- XP → Specified amount (or 0 if not specified)
- Level → Specified level (or 1 if not specified)

**Usage Examples:**
```
/resetxp @username
/resetxp 123456789 1000
/resetxp username123 5000 5
```

**Example Output:**
```
⭐ XP Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
⭐ Old XP: 15,000
🔄 New XP: 1,000
📊 Old Level: 8
🔄 New Level: 3

✅ XP and Level have been reset!
```

---

### **4. 💳 `/resetloan <username_or_id>`**
**Clear all active loans for a user**

**What it resets:**
- All active loans → Marked as "Cleared"

**Usage Examples:**
```
/resetloan @username
/resetloan 123456789
/resetloan username123
```

**Example Output:**
```
💳 Loan Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
🗑️ Loans Cleared: 2

✅ All active loans have been cleared!
```

---

### **5. 🎯 `/resetbets <username_or_id>`**
**Reset user betting data and milestones**

**What it resets:**
- Total Bets → 0
- All Milestones → False
- Betting Logs → Cleared (from all games)

**Usage Examples:**
```
/resetbets @username
/resetbets 123456789
/resetbets username123
```

**Example Output:**
```
🎯 Betting Data Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
📊 Total Bets: 0
🎁 All Milestones: Reset
🗑️ Betting Logs Cleared: 45

✅ Betting data has been completely reset!
```

---

### **6. 📅 `/resetdaily <username_or_id>`**
**Reset user daily claim data**

**What it resets:**
- Last Daily → Reset (can claim again)
- Daily Streak → 0

**Usage Examples:**
```
/resetdaily @username
/resetdaily 123456789
/resetdaily username123
```

**Example Output:**
```
📅 Daily Data Reset Complete!

👤 User: PlayerName
🆔 ID: 123456789
📅 Last Daily: Reset
🔥 Streak: 0

✅ Daily claim data has been reset!
```

---

## 🎯 **User Identification Methods**

All reset commands accept users in multiple formats:

### **Username (with or without @):**
```
/resetall @username
/resetall username
```

### **User ID (numeric):**
```
/resetall 123456789
```

### **Username without @:**
```
/resetall username123
```

---

## ⚠️ **Important Warnings**

### **⚠️ Irreversible Actions**
- **All reset operations are irreversible**
- **User data will be permanently lost**
- **No backup is created automatically**

### **🔐 Security Features**
- **Administrator-only access**
- **Full audit trail in bot logs**
- **User confirmation required for critical operations**

### **📊 Data Affected**
- **Users sheet** - User profile data
- **Logs_Loan** - Loan records
- **Logs_Aviator** - Aviator game logs
- **Logs_Spin** - Spin wheel game logs
- **Logs_RPS** - Rock Paper Scissors game logs
- **Logs_BetRewards** - Betting reward logs

---

## 🚀 **Use Cases**

### **1. 🆕 New User Setup**
```
/resetall @newuser
```
- Perfect for setting up new users with clean data

### **2. 🎮 Testing & Development**
```
/resetbalance @testuser 10000
/resetxp @testuser 5000 3
```
- Useful for testing different scenarios

### **3. 🔄 User Recovery**
```
/resetall @problemuser
```
- Reset problematic users to clean state

### **4. 🎯 Specific Resets**
```
/resetbets @user  # Reset only betting data
/resetdaily @user # Reset only daily claims
/resetloan @user  # Clear only loans
```

---

## 📝 **Best Practices**

### **✅ Do:**
- **Verify user identity** before resetting
- **Use specific commands** when possible instead of `/resetall`
- **Document resets** for audit purposes
- **Test on test accounts** first

### **❌ Don't:**
- **Reset active users** without warning
- **Use `/resetall`** when a specific reset would suffice
- **Reset multiple users** simultaneously without verification
- **Forget to check** if user has important data

---

## 🔧 **Technical Details**

### **Command Structure:**
```
/command <username_or_id> [optional_parameters]
```

### **Error Handling:**
- **User not found** → Clear error message
- **Invalid parameters** → Helpful usage instructions
- **Permission denied** → Administrator-only warning
- **Sheet errors** → Detailed error reporting

### **Performance:**
- **Efficient updates** using Google Sheets API
- **Batch operations** for multiple field updates
- **Error recovery** for partial failures

---

## 🎉 **Summary**

The admin reset commands provide **complete control** over user accounts, allowing administrators to:

- **🔄 Reset entire users** to starting state
- **💰 Reset specific balances** to any amount
- **⭐ Reset XP and levels** independently
- **💳 Clear active loans** for users
- **🎯 Reset betting progress** and milestones
- **📅 Reset daily claim data** for immediate access

All commands are **secure**, **efficient**, and **administrator-only**, ensuring safe management of the casino bot user base.

**Use these commands responsibly and always verify user identity before performing resets!** 🛡️
