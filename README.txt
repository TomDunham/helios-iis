HELIOS - supply chain sharing 
=============================

Ed Crewe and Tom Dunham - July 2011

A proof of concept demonstrator of how relief agencies can share supplies information
for helping distribute items in the field.

http://www.helios-foundation.org/cbha-project/index_html

The web system allows for plain CSV upload (or nightly import) of current supply details
and sharing and querying of that data for exchange of relief supplies.

Technical
---------

The system is written in django and comprises two custom eggs, iisharing, the main configuration
and web querying component and django-csvimport a generic tool for importing CSV files 
to django models.

Demo URL = http://www.helios-foundation.org/iisharing

Background
----------

This code was written for a (postponed) django-dash over the weekend of the 8 and 9th July 2011
by Tom and Ed. The House of Omni provided the workspace and the project was prompted by 
Fraser Stephens of the HELIOS foundation.
