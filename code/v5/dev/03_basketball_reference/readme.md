
## Classes

## Main class

### PageHTML

```python
href = '/'
```

```adruino
https://www.basketball-reference.com
├── /leagues/
│   ├── /leagues/NBA_2023.html
│   │   ├── /leagues/NBA_2023_games.html            # Games (of the first month by default)
│   │   ├── /leagues/NBA_2023_games-october.html    # Games happening in the first month 
│   │   ├── ...
│   │   └── /leagues/NBA_2023_games-june.html       # Games happening in the last month (POs)
│   ├── /leagues/NBA_2022_games.html
│   ├── ...
│   └── /leagues/BAA_1947_games.html
│
├── /teams/
│   ├── /teams/ATL/                         # Start of active franchises list
│   │   ├── /teams/ATL/2023.html                # Franchise latest season
│   │   │   ├── /teams/ATL/2023.html                    # Roster & Stats
│   │   │   ├── /teams/ATL/2023/gamelog/                # Gamelog
│   │   │   ├── /teams/ATL/2023/gamelog-advanced/       # Gamelog advanced
│   │   │   ├── /teams/ATL/2023/splits/                 # Splits
│   │   │   ├── /teams/ATL/2023/lineups/                # Lineups
│   │   │   ├── /teams/ATL/2023/on-off/                 # On-off
│   │   │   ├── /teams/ATL/2023_games.html              # Schedule
│   │   │   ├── /teams/ATL/2023_transactions.html       # Transactions
│   │   │   ├── /teams/ATL/2023_start.html              # Starting lineups
│   │   │   ├── /teams/ATL/2023_depth.html              # Depth charts
│   │   │   └── /teams/ATL/2023_referees.html           # Referees
│   │   ├── ...
│   │   └── /teams/TRI/1950.html                # Franchise first season
│   ├── ...
│   ├── teams/WAS/                          # End of active franchises list
│   ├── teams/AND/                          # Start of defunct franchises list
│   ├── ...
│   └── teams/WAT/                          # End of defunct franchises list
│
├── /boxscores/                                 # All boxscores                                      
│   ├── /boxscores/202304280LAL.html            # Boxscores of the latest game
│   │   ├── /boxscores/202304280LAL.html  
│   │   ├── /boxscores/pbp/202304280LAL.html        
│   │   ├── /boxscores/shot-chart/202304280LAL.html        
│   │   └── /boxscores/plus-minus/202304280LAL.html              
│   └── ...                                 
│   └── /boxscores/?month=12&day=25&year=2022   # Games played on a particular day
│       ├── /boxscores/202212250BOS.html
│       ├── ...
│       └── /boxscores/202212250DEN.html
│
├── /players/                               # All players
│   ├── /players/a/                             # All players last name starts with a
│   │   ├── ...                             
│   │   ├── /players/a/abdulka01.html              # Player page for Kareem Abdul-Jabbar
│   │   └── ...                  
│   ├── ...
│   └── /players/z/ 
```

## Indexes

### AllSeasonsIndexHTML

```python
href = '/leagues/'
```



### AllTeamsIndexHTML

```python
href = '/teams/'
```

### AllPlayersIndexHTML

```python
href = '/players/'
```

### AllBoxscoresIndexHTML

```python
href = '/boxscores/'                            # Current day
href = '/boxscores/?month=12&day=25&year=2022'  # Specific day
```

## Seasons

### SeasonIndexHTML

```python
href = '/leagues/NBA_2023.html'
```

### SeasonScheduleHTML

```python
href = '/leagues/NBA_2023_games.html'
href = '/leagues/NBA_2023_games-november.html'
```

## Teams

### TeamIndexHTML

```python
href = '/teams/GSW/'
```

### TeamSeasonIndexHTML

```python
href = '/teams/GSW/2023.html'
```



### TeamSeasonGamelogHTML

```python
href = '/teams/GSW/2023/gamelog/'
href = '/teams/GSW/2023/gamelog-advanced/'
```



## Players

### PlayersAlphabetHTML

```python
href = '/players/a/'
href = '/players/z/'
```

### PlayerIndexHTML

```python
href = '/players/c/curryst01.html'          # Stephen Curry
href = '/players/j/jamesle01.html'          # Lebron James
```

## Boxscores

### BoxscoresHTML

```python
href = '/boxscores/202212250DAL.html'       # LAL @ DAL boxscores
href = '/boxscores/202212250GSW.html'       # MEM @ GSW boxscores
```

### BoxscoresPbpHTML

```python
href = '/boxscores/pbp/202212250DAL.html'   # LAL @ DAL play-by-play
href = '/boxscores/pbp/202212250GSW.html'   # MEM @ GSW play-by-play
```

### BoxscoresShotchartHTML

```python
href = '/boxscores/shot-chart/202212250DAL.html'    # LAL @ DAL shot-chart
href = '/boxscores/shot-chart/202212250GSW.html'    # MEM @ GSW shot-chart
```

### BoxscoresPlusMinusHTML

```python
href = '/boxscores/plus-minus/202212250DAL.html'    # LAL @ DAL plus-minus
href = '/boxscores/plus-minus/202212250GSW.html'    # MEM @ GSW plus-minus
```
