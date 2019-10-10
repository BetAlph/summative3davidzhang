import csv
import os

from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

with open('movies.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    line_count = 0
    main = []
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            line_count += 1
            temp = []
            for col in row:
                temp.append(col)
            main.append(temp)
    db.execute('DROP TABLE movies')
    db.execute('CREATE TABLE movies (Title VARCHAR NOT NULL, Year VARCHAR NOT NULL, Runtime VARCHAR NOT NULL, imdbID VARCHAR NOT NULL, imdbRating VARCHAR NOT NULL, lowercase VARCHAR NOT NULL);')
    db.commit()
    for i in range(len(main)):
        a1 = main[i][0]
        a2 = main[i][1]
        a3 = main[i][2]
        a4 = main[i][3]
        a5 = main[i][4]
        a6 = main[i][0].lower()
        db.execute("INSERT INTO movies (Title, Year, Runtime, imdbID, imdbRating, lowercase) VALUES (:a1,:a2,:a3,:a4,:a5, :a6);", {"a1": a1,"a2": a2,"a3": a3,"a4": a4,"a5": a5,"a6": a6})
        db.commit()
        print("\n\n\n\nCREATING TABLE IN SQL DATABASE... \nPLEASE DO NOT CLOSE TERMINAL WINDOW!\n" + str(i) + " / " + str(len(main)) + "\n" + str(i/line_count*100) + " % Complete!")
    print("\n\n\n\nCREATING TABLE IN SQL DATABASE... \nPLEASE DO NOT CLOSE TERMINAL WINDOW!\n" + str(i) + " / " + str(len(main)) + "\n" + str(i/line_count*100) + " % Complete!")
    print("FINISHED CREATING TABLE IN SQL DATABASE!")
