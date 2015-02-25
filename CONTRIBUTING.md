# How to contribute

This project uses the "Fork & pull" collaborative model (see GitHub pull request documentation, link below).

You have to follow this steps to contribute:
* Create a [GitHub account](https://github.com)
* Fork the repository into your account on GitHub
* Clone the forked repository to your local machine; `git clone https://github.com/your_account/starling`
* Create a topic branch in the cloned repository (do not work on the master branch); `git checkout -b your_topic`
* Make your change in the cloned repository and commit
  * if you add a new module (block), add a test in the test.public directory
  * before commiting, run the tests; `tools/run_regression_tests.sh`
* Push the commit to the forked repository; `git push`
* Submit a pull request in GitHub from the forked repository

# Additional Resources

* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](https://help.github.com/articles/using-pull-requests)

