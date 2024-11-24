Hello! This is the updated application. It includes the following changes:

    Search functionality
    Reranking

These are the changes made:

    Added Whoosh for searches
        It indexes all the files and searches across them
        Searches support either wild card matching with an OR filter for matching any of the included words
        One idea I considered was adding completed:true or other basic filtering logic
    Added basic functionality to the app
        I added a X box to the search bar in order to cancel searches
    Added sort for titles
        I added the ability to sort tasks by title

Considerations for the future

A couple ideas that we could add in the future:

    Updated schema logic
        It might be nice to include the update and creation time in order to sort tasks by when they were created. It would also be helpful to start tracking users and projects if we plan to scale.

    Choosing a pagination scheme
        I thought that it might be nice to include pagination. We could paginate either by the number of results or do infinite scrolling. I could imagine a world where users have so many tasks that it slows down the page.

    Automatically searching on every letter
        Tools like Algolia allow you to update the search on every keystroke.

    Adding projects, attachments and other core building blocks for project management

    Indexes for the database tables
