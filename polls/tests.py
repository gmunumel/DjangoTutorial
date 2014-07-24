import datetime

from django.utils import timezone
from django.test import TestCase
from django.core.urlresolvers import reverse

from polls.models import Poll, Choice

# Create your tests here.
def create_poll(question, days):
  """
  Creates a poll with the given `question` published the given number of
  `days` offset to now (negative for polls published in the past,
  positive for polls that have yet to be published).
  """
  return Poll.objects.create(question=question,
            pub_date= timezone.now() + datetime.timedelta(days=days))

class PollViewTests(TestCase):
  def test_index_view_with_no_polls(self):
    """
    If no polls exist, an appropriate message should be displayed.
    """
    response = self.client.get(reverse('polls:index'))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "No polls are available.")
    self.assertQuerysetEqual(response.context['latest_poll_list'], [])

  def test_index_view_with_a_past_poll(self):
    """
    Polls with a pub_date in the past should be displayed on the index page.
    """
    create_poll(question="Past poll.", days=-30)
    response = self.client.get(reverse('polls:index'))
    self.assertQuerysetEqual(
      response.context['latest_poll_list'],
            ['<Poll: Past poll.>']
    )

  def test_index_view_with_a_future_poll(self):
    """
    Polls with a pub_date in the future should not be displayed on the
    index page.
    """
    create_poll(question="Future poll.", days=30)
    response = self.client.get(reverse('polls:index'))
    self.assertContains(response, "No polls are available.", status_code=200)
    self.assertQuerysetEqual(response.context['latest_poll_list'], [])

  def test_index_view_with_future_poll_and_past_poll(self):
    """
    Even if both past and future polls exist, only past polls should be
    displayed.
    """
    create_poll(question="Past poll.", days=-30)
    create_poll(question="Future poll.", days=30)
    response = self.client.get(reverse('polls:index'))
    self.assertQuerysetEqual(
        response.context['latest_poll_list'],
        ['<Poll: Past poll.>']
    )

  def test_index_view_with_two_past_polls(self):
    """
    The polls index page may display multiple polls.
    """
    create_poll(question="Past poll 1.", days=-30)
    create_poll(question="Past poll 2.", days=-5)
    response = self.client.get(reverse('polls:index'))
    self.assertQuerysetEqual(
        response.context['latest_poll_list'],
         ['<Poll: Past poll 2.>', '<Poll: Past poll 1.>']
    )

class PollIndexDetailTests(TestCase):
  def test_detail_view_with_a_future_poll(self):
    """
    The detail view of a poll with a pub_date in the future should
    return a 404 not found.
    """
    future_poll = create_poll(question='Future poll.', days=5)
    response = self.client.get(reverse('polls:detail', args=(future_poll.id,)))
    self.assertEqual(response.status_code, 404)

  def test_detail_view_with_a_past_poll(self):
    """
    The detail view of a poll with a pub_date in the past should display
    the poll's question.
    """
    past_poll = create_poll(question='Past Poll.', days=-5)
    response = self.client.get(reverse('polls:detail', args=(past_poll.id,)))
    self.assertContains(response, past_poll.question, status_code=200)

class PollResultsTests(TestCase):
  def test_results_view_with_a_future_poll(self):
    """
    The results view of a poll with a pub_date in the future should
    return a 404 not found.
    """
    future_poll = create_poll(question='Future poll.', days=5)
    response = self.client.get(reverse('polls:results', args=(future_poll.id,)))
    self.assertEqual(response.status_code, 404)

  def test_results_view_with_a_past_poll(self):
    """
    The results view of a poll with a pub_date in the past should display
    the poll's question.
    """
    past_poll = create_poll(question='Past Poll.', days=-5)
    response = self.client.get(reverse('polls:results', args=(past_poll.id,)))
    self.assertContains(response, past_poll.question, status_code=200)

class PollVoteTests(TestCase):
  def test_votes_view_with_a_non_existing_poll(self):
    """
    The votes view of a non-existing poll (42) returns 404 
    """
    response = self.client.post(reverse('polls:vote', args=(42,)))
    self.assertEqual(response.status_code, 404)

  def test_votes_view_with_a_poll_but_no_choice(self):
    """
    The votes view of a poll but with not a choice
    """
    poll = create_poll(question='My poll.', days=5)
    response = self.client.post(reverse('polls:vote', args=(poll.id,)))
    self.assertContains(response, "You didn&#39;t select a choice.", status_code=200)

  def test_votes_view_with_a_poll(self):
    """
    The votes view of a poll 
    """
    poll = create_poll(question='My poll.', days=5)
    choice_a = Choice.objects.create(poll=poll, choice_text='Awesome!', votes=0)
    choice_b = Choice.objects.create(poll=poll, choice_text='Good', votes=0)
    choice_c = Choice.objects.create(poll=poll, choice_text='Bad', votes=0)
    response = self.client.post(reverse('polls:vote', args=(poll.id,)), {'choice': choice_a.id})

    # check i'm redirected
    self.assertEquals(response.status_code, 302)

    # checking the new voted choice of a
    new_choice_a = Choice.objects.get(pk=choice_a.id)
    self.assertEquals(new_choice_a.votes, 1)

class PollMethodTests(TestCase):
  def test_was_published_recently_with_future_poll(self):
    """
    was_published_recently() should return False for polls whose pub_date is in the future
    """
    future_poll = Poll(pub_date=timezone.now() + datetime.timedelta(days=30))
    self.assertEqual(future_poll.was_published_recently(), False)

  def test_was_published_recently_with_old_poll(self):
    """
    was_published_recently() should return False for polls whose pub_date is older than 1 day
    """
    old_poll = Poll(pub_date=timezone.now() - datetime.timedelta(days=30))
    self.assertEqual(old_poll.was_published_recently(), False)

  def test_was_published_recently_with_recent_poll(self):
    """
    was_published_recently() should return True for polls whose pub_date is within the last day
    """
    recent_poll = Poll(pub_date=timezone.now() - datetime.timedelta(hours=1))
    self.assertEqual(recent_poll.was_published_recently(), True)

  def test_unicode(self):
    """
    __unicode__ should return the text of poll
    """
    poll = create_poll(question='Poll', days=-5)
    self.assertEqual(poll.__unicode__(), 'Poll')

class ChoiceMethodTests(TestCase):
  def test_unicode(self):
    """
    __unicode__ should return the text of choice
    """
    poll = create_poll(question='Poll', days=-5)
    choice = Choice(poll=poll, choice_text='Awesome!', votes=5)
    self.assertEqual(choice.__unicode__(), 'Awesome!')
