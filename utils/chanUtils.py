import discord
import re
import basc_py4chan

def posttoembed(post, thumbnail=True):
    threadidfrompost = re.match(r'http://boards.4chan.org/vg/thread/([0-9]{9})#p', post.url).group(1)
    rawcomment = post.comment
    textcomment = post.text_comment
    innermatches = re.findall(r'<a href="#p(.*?)" class="quotelink">', rawcomment)
    outermatches = re.findall(r'<a href="/vg/thread/[0-9]{9}#p([0-9]{9})', rawcomment)
    outermatchurl = re.findall(r'<a href="/(.*?)" class="quotelink">', rawcomment)
    for m in innermatches:
        textcomment = textcomment.replace('>>{}'.format(m),
                                          '[>>{id}](http://boards.4chan.org/vg/thread/{threadid}#p{id})'.format(id=m,
                                                                                                                threadid=threadidfrompost))
    for (i, m) in enumerate(outermatches):
        textcomment = textcomment.replace('>>{}'.format(m),
                                          '[>>{}](http://boards.4chan.org/vg/thread/{})'.format(m, outermatchurl[i]))

    if len(textcomment) > 2047:
        textcomment = textcomment[:2030] + '**...(cutoff)**'
    em = discord.Embed(description=textcomment, colour=0xD6DAF0, timestamp=post.datetime,
                       title='No. {}'.format(str(post.post_id)), url=post.url)
    em.set_author(name=post.name)
    if post.has_file:
        if thumbnail:
            em.set_thumbnail(url=post.file.thumbnail_url.replace('http://', 'https://'))
        else:
            em.set_image(url=post.file.file_url.replace('http://', 'https://'))
        em.set_footer(text=post.file.filename_original)
    return em


def getthread(boardname='vg', threadname='/tfg'):
    board = basc_py4chan.Board(boardname)
    threads = board.get_all_threads()
    for thread in threads:
        if thread.topic.subject is not None:
            if threadname in thread.topic.subject:
                return board.get_thread(thread.id)
                break