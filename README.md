# CatScan Checker

This is the backend for [CatScan 🐱](https://scan.jacow.org/) and designed to run on [Digital Ocean](https://www.digitalocean.com/) as an App Service using the Functions feature. This is to make use of their free tier.

The application is broken up into several 7 microservices described below. 

These handle contributions on Indico:

1. Notify - Gets notified by indico when a new contribution is added, and adds items to the queue. These are send via the notify service in [openreferee-jacow](https://github.com/indico/openreferee-jacow)
2. Finder - Sometimes items are missed, finder will scan each day to find any missing items (midnight) and add them to the queue
3. Worker - Queue worker, sends off scans to the LaTeX or Word Checker

This is the service that  on the CatScan frontend

4. Conferences - Lists future conferences (from [Reference Search](https://refs.jacow.org/))

These are the checkers:

5. Word - Microsoft Word Checker
6. LaTeX (Deprecated) - Old LaTeX checker, replaced with [catscan-latex](https://github.com/joshpme/catscan-latex)
7. Cleanup - Garbage collector for any files that didn't clean up successfully.

## Work Checker

CatScan is hosted on DO and functions can only handle payloads of 1mb.
See https://docs.digitalocean.com/products/functions/details/limits/

So the CatScan interface uploads the word file directly to the DO space (storage bucket) and then sends a notification to the word scanner where the file is.

The storage bucket is configured as a write-only dropbox. So regular users cannot see the content put their. This is specified in the policy.json file.

After the scan is performed the storage bucket object is removed, and cleanup is run periodically in the case that the word scanner failed to remove the object.

Word Scanning can also be performed directly on items in the JACoW Indico. An authenticated request (typically performed by the worker) with a contribution + revision numbers. As well as outputting the results, the output also includes a `"filename"` where the results are held indefinitely in object storage. The filenames are calculated as the hash of the scan results. These can be retrieved by supplying the payload `"results"` to the word service.

## LaTeX Checker (Deprecated)

The LaTeX checker was moved to its own repository as DO functions cannot handler newer versions of Go, which is required for the comment generation. See [catscan-latex](https://github.com/joshpme/catscan-latex)