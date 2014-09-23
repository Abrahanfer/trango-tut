from django.template import RequestContext
from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm

# Create your views here.
def index(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    #context = RequestContext(request)
    # NOT ANYMORE WITH RENDER

    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be
    # passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages': page_list}

    # The following two lines are new.
    # We loop through each category returned, and create a URL
    # attribute. This attribute stores an encoded URL (e.g. spaces
    # replaced with underscores).
    for category in category_list:
        category.url = Category.encode(category.name)

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return render(request, 'rango/index.html', context_dict)

def about(request):
    #context = RequestContext(request)
    # NOT ANYMORE WITH RENDER

    context_dictionary = {'aboutmessage': "Stalin el mejón"}

    return render(request, 'rango/about.html', context_dictionary)

def category(request, category_name_url):
     # Request our context from the request passed to us.
    #context = RequestContext(request)
    # NOT ANYMORE WITH RENDER

    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to
    # get the name.
    category_name = Category.decode(category_name_url)

    # Create a context dictionary which we can pass to the template
    # rendering engine. We start by containing the name of the
    # category passed by the user.
    context_dict = {'category_name': category_name}
    context_dict['category_name_url'] = category_name_url
    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist
        # exception. So the .get() method returns one model instance
        # or raises an exception.
        category = Category.objects.get(name=category_name)

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)

        # Adds our results list to the template context under name
        # pages.
        context_dict['pages'] = pages

        # We also add the category object from the database to the
        # context dictionary. We'll use this in the template to verify
        # that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category"
        # message for us.
        return add_category(request)

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    #A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print(form.errors)
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_url):

    category_name = Category.decode(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit straight away.
            # Not all fields are automatically populated!
            page = form.save(commit=False)

            # Retrieve the associated Category object so we can add it.
            # Wrap the code in a try block - check if the category actually exists!
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                # If we get here, the category does not exist.
                # Go back and render the add category form as a way of saying the category does not exist.
                return render(request, 'rango/add_category.html', {})

            # Also, create a default value for the number of views.
            page.views = 0

            # With this, we can then save our new model instance.
            page.save()

            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print(form.errors)
    else:
        form = PageForm()

    return render(request, 'rango/add_page.html',
            {'category_name_url': category_name_url,
             'category_name': category_name, 'form': form})
