# Configuration
After completing the installation steps for this bot and starting it, you'll need to configure it.  

## Executing SQL commands
Configuration of this bot is almost entirely SQL based. 
To execute an SQL command, type `-sql ` followed by an SQL command you wish to execute

## Member verification
Member verification is country based. To configure the default country role, you can use the following SQL command
```sqlite
INSERT INTO roles VALUES ('default_country', 216149444733829120, 410868129825030145)
```
Replace the first number with the server/guild ID, replace the second number with the role ID.  

---

To configure a country specific role, type
```sqlite
INSERT INTO country_roles VALUES ('GE', 216149444733829120, 412328316696133644)
```
First field is an Alpha-2 code of the country, second is the server/guild ID and third is the role ID.  

---

A new member needs to link their profile somewhere. That somewhere is called a verification channel. 
To configure a verification channel, type 
```sqlite
INSERT INTO channels VALUES ('verify', 216149444733829120, 727784609890172989)
```
Replace the first number with the server/guild ID, replace the second number with the channel ID.  
**This specific change requires a restart to apply**

---
## PP roles
This is an optional feature and can be left disabled if desired. You can use the following SQL command to configure
```sqlite
INSERT INTO pp_roles VALUES (1000, 216149444733829120, 418807617629061121)
```
first number is pp amount, second is server/guild ID, third is role ID.  
You do this for every 1000 pp
