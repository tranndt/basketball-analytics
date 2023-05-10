import sys
sys.path.insert(0,'../../')
import main

if __name__ == "__main__":
    LOCAL_HOST = '/Volumes/Seagate Portable Disk/University of Manitoba/Data Science/Datasets/basketball-analytics/https:/www.basketball-reference.com'
    db = main.DatabaseManager(LOCAL_HOST)
    print(db.info())

    page = main.AllSeasonsIndexHTML()
    page.fetch()

    for href in page.downstream_hrefs()[27:]:
        print(href)
        db.sync_downstream(href,new_files_only=True,content_only=True,downstream=True,wait=3)

