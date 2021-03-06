from django.template import RequestContext
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from rango.models import Category
from rango.models import Page, UserProfile
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm

#helper function to get category list
def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = Category.encode(cat.name)

    return cat_list

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
    cat_list = get_category_list()
    context_dict = {'categories': category_list, 'pages': page_list,
                    'cat_list': cat_list}
    # The following two lines are new.
    # We loop through each category returned, and create a URL
    # attribute. This attribute stores an encoded URL (e.g. spaces
    # replaced with underscores).
    for category in category_list:
        category.url = Category.encode(category.name)

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.

     # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, we default to zero and cast that.
    visits = int(request.COOKIES.get('visits', '0'))
    if request.session.get('last_visit'):
        # The session has a value for The last visit
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    # Return response back to the user, updating any cookies that need
    # changed.
    response = render(request, 'rango/index.html', context_dict)
    return response

def about(request):
    #context = RequestContext(request)
    # NOT ANYMORE WITH RENDER
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    about_string = "Stalin es el mejon. Repitelo " + str(count) + "veces"
    cat_list = get_category_list()
    context_dictionary = {'aboutmessage': about_string, 'cat_list':
                          cat_list }

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
    cat_list = get_category_list()
    context_dict = {'category_name': category_name, 'cat_list':
                    cat_list}
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

        #Adding likes of category to context dictionary
        context_dict['category_likes'] = category.likes
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category"
        # message for us.
        return add_category(request)

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)

@login_required
def like_category(request):
    results = 0
    if request.method == 'GET':
        if 'category_id' in request.GET:
            category_id = request.GET['category_id']
            category = Category.objects.get(pk=category_id)
            if category:
                category.likes = category.likes + 1
                category.save()
                results = category.likes

    return HttpResponse(results)

@login_required
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

@login_required
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

    cat_list = get_category_list()
    return render(request, 'rango/add_page.html',
            {'category_name_url': category_name_url,
             'category_name': category_name, 'cat_list': cat_list,
             'form': form})


def register(request):
    # Like before, get the request's context.
    #context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print(user_form.errors, profile_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    cat_list = get_category_list()
    # Render the template depending on the context.
    return render(request,
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form,
             'registered': registered, 'cat_list': cat_list })

def user_login(request):
    # Like before, obtain the context for the user's request.
    #context = RequestContext(request)
    cat_list = get_category_list()
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print("Invalid login details: {0}, {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html', {'cat_list': cat_list})

@login_required
def restricted(request):
    cat_list = get_category_list()
    return render(request, 'rango/restricted.html',
                  {'restricted_msg':
                   "Since you're logged in, you can see this text!",
                   'cat_list': cat_list})

# Use the login_required() decorator to ensure only those logged in
# can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')

@login_required
def profile(request):
    user_local = request.user
    context_dict = {'username': user_local.username, 'email':
                        user_local.email}
    profile_user_query=UserProfile.objects.filter(user__username=user_local.username)
    if len(profile_user_query) > 0:
        profile_user = profile_user_query[0]
        context_dict['website']=profile_user.website
        print(profile_user.picture)
        context_dict['user_picture']=profile_user.picture

    return render(request, 'rango/profile.html', context_dict)

def track_url(request):
    if request.method == 'GET':
        if 'page_id' in request.GET:
            pk_page = request.GET['page_id']
            page_array = Page.objects.filter(pk=pk_page)

            if len(page_array) > 0:
                page = page_array[0]
                page.views = page.views + 1
                page.save()

                return HttpResponseRedirect(page.url)
        else:
            return HttpResponseBadRequest
    else:
        return HttpResponseNotFound

def suggest_category(request):
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/category_list.html', {'cat_list': cat_list })
