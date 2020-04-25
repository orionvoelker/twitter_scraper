import twint

c = twint.Config()
c.Username = "adhd_superpower"
c.Output = "tweets.csv"
c.Store_csv= True

twint.run.Favorites(c)
