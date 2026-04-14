Windows PC (after any change):
powershellgit add .
git commit -m "describe change"
git push origin master
Server:
bashcd /opt/hotel-carrental
git pull origin master
systemctl restart hotel-carrental
Now go check your live site — https://carrental.sandshotel.us 🎉ok sir...10:54 AMCongratulations! 🎉 Your car rental site is live at https://carrental.sandshotel.us!
Here's a summary of everything you built:
Customer site:

Browse fleet of 6 vehicles
Search by type and dates
3-step booking form
Confirmation page with booking reference
Status check page

Admin panel (/admin):

Dashboard with stats
Approve or decline bookings
Manage fleet status
Generate PDF rental agreements
Add new vehicles

Tech stack:

Python Flask + Gunicorn
MariaDB database
Nginx reverse proxy
Let's Encrypt SSL
GitHub for deployments

Whenever you need to add features — payment integration, email notifications, customer portal — just come back and we'll build it! 🚗

Server Access : ssh root@129.121.85.32